from logging import getLogger
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from scr.models.script import Script
from scr.models.execution import Execution

logger = getLogger(__name__)

class ScriptRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_script(
        self, 
        user_id: int, 
        name: str, 
        code: str, 
        description:  Optional[str], 
        schedule: Optional[str]
    ) -> Script:
        """Создать новый скрипт"""
        logger.info(f"creating script '{name}' for user {user_id}")
        
        script = Script(
            user_id=user_id,
            name=name,
            description=description,
            code=code,
            schedule=schedule, 
            is_active=True
        )
        
        try:
            self.db.add(script)
            await self.db.commit()
            await self.db.refresh(script)
            logger.info(f"script created with id {script.id}")
            return script
        except Exception as e:
            await self.db.rollback()
            logger.error(f"error creating script: {e}")
            raise
    
    async def get_script(self, script_id: int, user_id: int) -> Optional[Script]:
        logger.info(f"getting script {script_id} for user {user_id}")
        
        query = select(Script).where(
            Script.id == script_id,
            Script.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_scripts(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Script]:
        logger.info(f"getting scripts for user {user_id}")
        
        query = select(Script).where(Script.user_id == user_id)
        
        if not include_inactive:
            query = query.where(Script.is_active == True)
        
        query = query.order_by(desc(Script.created_at)).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def update_script(
        self, 
        script_id: int, 
        user_id: int, 
        update_data: dict
    ) -> Optional[Script]:
        logger.info(f"updating script {script_id}")
        
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            return await self.get_script(script_id, user_id)
        
        query = (
            update(Script)
            .where(Script.id == script_id, Script.user_id == user_id)
            .values(**update_data, updated_at=datetime.utcnow())
            .returning(Script)
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        script = result.scalar_one_or_none()
        if script:
            logger.info(f"script {script_id} updated")
        return script
    
    async def delete_script(self, script_id: int, user_id: int) -> bool:
        logger.info(f"deleting script {script_id}")
        
        query = delete(Script).where(
            Script.id == script_id,
            Script.user_id == user_id
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"script {script_id} deleted")
        return deleted
    
    async def update_script_last_run(self, script_id: int, last_run_at: datetime):
        query = (
            update(Script)
            .where(Script.id == script_id)
            .values(last_run_at=last_run_at)
        )
        await self.db.execute(query)
        await self.db.commit()
    
    async def toggle_script_active(self, script_id: int, user_id: int, is_active: bool) -> bool:
        query = (
            update(Script)
            .where(Script.id == script_id, Script.user_id == user_id)
            .values(is_active=is_active)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0
    
    async def create_execution(self, script_id: int) -> Execution:
        logger.info(f"creating execution record for script {script_id}")
        
        execution = Execution(
            script_id=script_id,
            status="running",
            started_at=datetime.utcnow()
        )
        
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        
        return execution
    
    async def update_execution(
        self,
        execution_id: int,
        status: str,
        output:  Optional[str],
        error:  Optional[str],
        finished_at: Optional[datetime],
        duration_ms: Optional[int]
    ):
        logger.info(f"updating execution {execution_id} with status {status}")
        
        update_data = {"status": status}
        
        if output is not None:
            update_data["output"] = output
        if error is not None:
            update_data["error"] = error
        if finished_at is not None:
            update_data["finished_at"] = finished_at
        if duration_ms is not None:
            update_data["duration_ms"] = duration_ms
        
        query = (
            update(Execution)
            .where(Execution.id == execution_id)
            .values(**update_data)
        )
        
        await self.db.execute(query)
        await self.db.commit()
    
    async def get_script_executions(
        self, 
        script_id: int, 
        user_id: int, 
        limit: int = 50
    ) -> List[Execution]:
        logger.info(f"getting executions for script {script_id}")
        
        script = await self.get_script(script_id, user_id)
        if not script:
            return []
        
        query = (
            select(Execution)
            .where(Execution.script_id == script_id)
            .order_by(desc(Execution.started_at))
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_execution(self, execution_id: int, user_id: int) -> Optional[Execution]:
        query = (
            select(Execution)
            .join(Script, Execution.script_id == Script.id)
            .where(Execution.id == execution_id, Script.user_id == user_id)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()