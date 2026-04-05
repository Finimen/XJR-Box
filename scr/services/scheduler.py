import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from scr.models.script import Script
from scr.services.script import ScriptService
from scr.repositories.scripts_repository import ScriptRepository

logger = logging.getLogger(__name__)

class ScriptScheduler:
    def __init__(self, session_factory): 
        self.session_factory = session_factory
        self._tasks: Dict[int, dict] = {}
        self._running = False
        self._scheduler_task = None
    
    async def start(self):
        logger.info("=" * 50)
        logger.info("Starting simple scheduler...")
        logger.info("=" * 50)
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        await self.load_all_scripts()
        logger.info("Simple scheduler started")
    
    async def shutdown(self):
        logger.info("Shutting down scheduler...")
        self._running = False
        
        for task in self._tasks.values():
            task.cancel()
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
        
        logger.info("Scheduler stopped")
    
    async def _scheduler_loop(self):
        logger.info("Scheduler loop started")
        
        while self._running:
            try:
                now = datetime.now()
                
                for script_id, task_info in list(self._tasks.items()):
                    next_run = task_info.get('next_run')
                    schedule = task_info.get('schedule')
                    
                    if next_run and now >= next_run:
                        next_run_time = self._calculate_next_run(schedule, now)
                        self._tasks[script_id]['next_run'] = next_run_time
                        
                        logger.info(f"🕐 SCHEDULER TRIGGERED at {now} for script {script_id}")
                        asyncio.create_task(self._execute_script_job(script_id))
                
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(5)
    
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
                        logger.info(f"✅ Scheduled script: {script.name} (id={script.id}) with schedule: {script.schedule}")
        except Exception as e:
            logger.error(f"Failed to load scripts: {e}")
            import traceback
            traceback.print_exc()
    
    async def add_job(self, script: Script):
        if not script.schedule:
            return
        
        await self.remove_job(script.id)
        
        now = datetime.now()
        next_run = self._calculate_next_run(script.schedule, now)
        
        self._tasks[script.id] = {
            'schedule': script.schedule,
            'next_run': next_run,
            'script_name': script.name
        }
        
        logger.info(f"✅ Job added: script_{script.id}, next run: {next_run}")
    
    async def remove_job(self, script_id: int):
        if script_id in self._tasks:
            del self._tasks[script_id]
            logger.info(f"Removed job for script {script_id}")
    
    async def update_job(self, script: Script):
        if script.is_active and script.schedule:
            await self.add_job(script)
        else:
            await self.remove_job(script.id)
    
    async def _execute_script_job(self, script_id: int):
        try:
            async with self.session_factory() as session:
                repo = ScriptRepository(session)
                script_service = ScriptService(repo)
                
                script = await script_service.get_script_by_id(script_id)
                if not script:
                    logger.warning(f"Script {script_id} not found")
                    return
                
                if not script.is_active:
                    logger.warning(f"Script {script_id} is inactive")
                    return
                
                logger.info(f"🚀 Running scheduled script: {script.name} (id={script_id})")
                execution_id = await script_service.run_script_by_id(script_id)
                logger.info(f"✅ Script {script_id} started, execution_id={execution_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to execute script {script_id}: {e}")
            import traceback
            traceback.print_exc()
    
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
            except:
                pass
        
        if schedule.endswith("s"):
            try:
                seconds = int(schedule[:-1])
                return from_time + timedelta(seconds=seconds)
            except:
                pass
        elif schedule.endswith("m"):
            try:
                minutes = int(schedule[:-1])
                return from_time + timedelta(minutes=minutes)
            except:
                pass
        elif schedule.endswith("h"):
            try:
                hours = int(schedule[:-1])
                return from_time + timedelta(hours=hours)
            except:
                pass
        
        parts = schedule.split()
        if len(parts) == 5:
            minute = parts[0]
            if minute.startswith("*/"):
                try:
                    interval = int(minute[2:])
                    return from_time + timedelta(minutes=interval)
                except:
                    pass
        
        logger.warning(f"Unrecognized schedule format: {schedule}, using 1 minute default")
        return from_time + timedelta(minutes=1)
    
    async def get_all_jobs(self):
        jobs = []
        for script_id, info in self._tasks.items():
            jobs.append({
                "id": f"script_{script_id}",
                "next_run_time": str(info['next_run']) if info['next_run'] else None,
                "trigger": info['schedule'],
                "script_name": info['script_name']
            })
        return jobs