import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncio
from scr.models.script import Script
from scr.repositories.scripts_repository import ScriptRepository

class ScriptService:
    def __init__(self, script_repo: ScriptRepository):
        self.script_repo = script_repo
    
    async def create_script(self, user_id: int, name: str, code: str, description: Optional[str], schedule: Optional[str]) -> Script:
        return await self.script_repo.create_script(
            user_id=user_id,
            name=name,
            description=description,
            code=code,
            schedule=schedule
        )
    
    async def run_script_now(self, script_id: int, user_id: int, background_tasks) -> int:
        script = await self.script_repo.get_script(script_id, user_id)
        if not script:
            raise ValueError("Script not found")
        
        execution = await self.script_repo.create_execution(script_id)
        
        background_tasks.add_task(self._execute_script, script, execution.id)
        
        return execution.id
    
    async def _execute_script(self, script: Script, execution_id: int):
        started_at = datetime.utcnow()
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script.code)
                temp_path = f.name
            
            process = await asyncio.create_subprocess_exec(
                "python", temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=30  # 30 секунд таймаут
                )
                
                status = "success" if process.returncode == 0 else "failed"
                output = stdout.decode()
                error = stderr.decode()
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                status = "timeout"
                output = ""
                error = f"Script timeout after 30 seconds"
            
            finished_at = datetime.utcnow()
            duration_ms = int((finished_at - started_at).total_seconds() * 1000)
            
            await self.script_repo.update_execution(
                execution_id=execution_id,
                status=status,
                output=output,
                error=error,
                finished_at=finished_at,
                duration_ms=duration_ms
            )
            
            await self.script_repo.update_script_last_run(script.id, started_at)
            
        except Exception as e:
            await self.script_repo.update_execution(
                execution_id=execution_id,
                status="error",
                error=str(e),
                finished_at=datetime.utcnow()
            )
        finally:
            if 'temp_path' in locals():
                Path(temp_path).unlink(missing_ok=True)
