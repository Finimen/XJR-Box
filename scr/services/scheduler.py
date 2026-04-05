import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from heapq import heappush, heappop

from scr.models.script import Script
from scr.services.script import ScriptService
from scr.repositories.scripts_repository import ScriptRepository
from scr.services.redis import RedisService

logger = logging.getLogger(__name__)

class ScriptScheduler:
    def __init__(self, session_factory, redis_service: RedisService):
        self.session_factory = session_factory
        self.redis_service = redis_service
        self._jobs: Dict[int, 'ScheduledJob'] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._event = asyncio.Event()  
    
    async def start(self):
        logger.info("Starting optimized scheduler...")
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        await self.load_all_scripts()
        logger.info("Scheduler started")
    
    async def shutdown(self):
        logger.info("Shutting down scheduler...")
        self._running = False
        self._event.set()  
        
        if self._scheduler_task:
            try:
                await asyncio.wait_for(self._scheduler_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._scheduler_task.cancel()
                logger.warning("Scheduler task cancelled due to timeout")
        
        self._jobs.clear()
        logger.info("Scheduler stopped")
    
    async def _scheduler_loop(self):
        logger.info("Scheduler loop started")
        
        while self._running:
            try:
                next_run_time = self._get_next_run_time()
                
                if next_run_time is None:
                    try:
                        await asyncio.wait_for(self._event.wait(), timeout=60.0)
                        self._event.clear()
                    except asyncio.TimeoutError:
                        continue
                else:
                    now = datetime.now()
                    wait_seconds = (next_run_time - now).total_seconds()
                    
                    if wait_seconds <= 0:
                        await self._execute_due_jobs()
                    else:
                        try:
                            await asyncio.wait_for(self._event.wait(), timeout=min(wait_seconds, 60.0))
                            self._event.clear()
                        except asyncio.TimeoutError:
                            pass  
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}", exc_info=True)
                await asyncio.sleep(1)  # Пауза при ошибке
    
    def _get_next_run_time(self) -> Optional[datetime]:
        if not self._jobs:
            return None
        
        next_time = None
        for job in self._jobs.values():
            if job.next_run and (next_time is None or job.next_run < next_time):
                next_time = job.next_run
        return next_time
    
    async def _execute_due_jobs(self):
        now = datetime.now()
        due_jobs = []
        
        for script_id, job in list(self._jobs.items()):
            if job.next_run and job.next_run <= now:
                due_jobs.append((script_id, job))
        
        for script_id, job in due_jobs:
            job.next_run = self._calculate_next_run(job.schedule, now)
            logger.info(f"🕐 Executing scheduled script {script_id}, next run at {job.next_run}")
            
            asyncio.create_task(self._execute_script_job(script_id))
    
    async def load_all_scripts(self):
        try:
            async with self.session_factory() as session:
                repo = ScriptRepository(session)
                script_service = ScriptService(repo)
                scripts = await script_service.get_all_active_scripts()
                
                logger.info(f"Found {len(scripts)} active scripts with schedules")
                
                for script in scripts:
                    if script.schedule and script.is_active:
                        await self.add_job(script)
                        logger.info(f"✅ Scheduled script: {script.name} (id={script.id})")
        except Exception as e:
            logger.error(f"Failed to load scripts: {e}", exc_info=True)
    
    async def add_job(self, script: Script):
        if not script.schedule:
            return
        
        await self.remove_job(script.id)
        
        now = datetime.now()
        next_run = self._calculate_next_run(script.schedule, now)
        
        self._jobs[script.id] = ScheduledJob(
            script_id=script.id,
            schedule=script.schedule,
            next_run=next_run,
            script_name=script.name
        )
        
        self._event.set()
        
        logger.info(f"✅ Job added: script_{script.id}, next run: {next_run}")
    
    async def remove_job(self, script_id: int):
        if script_id in self._jobs:
            del self._jobs[script_id]
            self._event.set()  # Пробуждаем для перерасчета времени
            logger.info(f"Removed job for script {script_id}")
    
    async def update_job(self, script: Script):
        if script.is_active and script.schedule:
            await self.add_job(script)
        else:
            await self.remove_job(script.id)
    
    async def _execute_script_job(self, script_id: int):
        # Используем Redis для распределенной блокировки
        lock_key = f"script:execution:{script_id}"
        lock_acquired = await self.redis_service.acquire_lock(
            lock_key, 
            timeout=60  # Блокировка на 60 секунд
        )
        
        if not lock_acquired:
            logger.warning(f"Script {script_id} is already running, skipping...")
            return
        
        try:
            async with self.session_factory() as session:
                repo = ScriptRepository(session)
                script_service = ScriptService(repo)
                
                script = await script_service.get_script_by_id(script_id)
                if not script or not script.is_active:
                    logger.warning(f"Script {script_id} not found or inactive")
                    return
                
                logger.info(f"🚀 Running scheduled script: {script.name} (id={script_id})")
                execution_id = await script_service.run_script_by_id(script_id)
                logger.info(f"✅ Script {script_id} started, execution_id={execution_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to execute script {script_id}: {e}", exc_info=True)
        finally:
            await self.redis_service.release_lock(lock_key)
    
    def _calculate_next_run(self, schedule: str, from_time: datetime) -> datetime:
        schedule = schedule.strip().lower()
        
        if schedule.startswith("interval:"):
            try:
                value = schedule.split(":")[1]
                if value.endswith("s"):
                    seconds = int(value[:-1])
                    return from_time + timedelta(seconds=seconds)
                elif value.endswith("m"):
                    minutes = int(value[:-1])
                    return from_time + timedelta(minutes=minutes)
                elif value.endswith("h"):
                    hours = int(value[:-1])
                    return from_time + timedelta(hours=hours)
            except (IndexError, ValueError):
                pass
        
        if schedule.endswith("s"):
            try:
                seconds = int(schedule[:-1])
                return from_time + timedelta(seconds=seconds)
            except ValueError:
                pass
        elif schedule.endswith("m"):
            try:
                minutes = int(schedule[:-1])
                return from_time + timedelta(minutes=minutes)
            except ValueError:
                pass
        elif schedule.endswith("h"):
            try:
                hours = int(schedule[:-1])
                return from_time + timedelta(hours=hours)
            except ValueError:
                pass
        
        # TODO: Добавить поддержку cron через библиотеку croniter
        # from croniter import croniter
        # return croniter(schedule, from_time).get_next(datetime)
        
        logger.warning(f"Unrecognized schedule format: {schedule}, using 1 minute default")
        return from_time + timedelta(minutes=1)
    
    async def get_all_jobs(self) -> List[dict]:
        return [
            {
                "id": f"script_{script_id}",
                "next_run_time": str(job.next_run) if job.next_run else None,
                "trigger": job.schedule,
                "script_name": job.script_name
            }
            for script_id, job in self._jobs.items()
        ]


class ScheduledJob:
    def __init__(self, script_id: int, schedule: str, next_run: datetime, script_name: str):
        self.script_id = script_id
        self.schedule = schedule
        self.next_run = next_run
        self.script_name = script_name