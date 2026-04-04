from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List
from scr.core.di import get_script_service, get_current_user
from scr.schemas.execution import ExecutionResponse
from scr.schemas.script import ScriptCreate, ScriptUpdate, ScriptResponse
from scr.services.script import ScriptService
from scr.models.user_model import UserModel

router = APIRouter(prefix="/scripts", tags=["scripts"])

@router.post("/", response_model=ScriptResponse, status_code=201)
async def create_script(
    script_data: ScriptCreate,
    current_user: UserModel = Depends(get_current_user),
    script_service: ScriptService = Depends(get_script_service)
):
    script = await script_service.create_script(
        user_id=current_user.id,
        name=script_data.name,
        description=script_data.description,
        code=script_data.code,
        schedule=script_data.schedule
    )
    return script

@router.get("/", response_model=List[ScriptResponse])
async def list_scripts(
    current_user: UserModel = Depends(get_current_user),
    script_service: ScriptService = Depends(get_script_service),
    skip: int = 0,
    limit: int = 100
):
    scripts = await script_service.get_user_scripts(current_user.id, skip, limit)
    return scripts

@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    current_user: UserModel = Depends(get_current_user),
    script_service: ScriptService = Depends(get_script_service)
):
    script = await script_service.get_script(script_id, current_user.id)
    if not script:
        raise HTTPException(404, "Script not found")
    return script

@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: int,
    script_data: ScriptUpdate,
    current_user: UserModel = Depends(get_current_user),
    script_service: ScriptService = Depends(get_script_service)
):
    script = await script_service.update_script(
        script_id, 
        current_user.id, 
        script_data.dict(exclude_unset=True)
    )
    if not script:
        raise HTTPException(404, "Script not found")
    return script

@router.delete("/{script_id}", status_code=204)
async def delete_script(
    script_id: int,
    current_user: UserModel = Depends(get_current_user),
    script_service: ScriptService = Depends(get_script_service)
):
    deleted = await script_service.delete_script(script_id, current_user.id)
    if not deleted:
        raise HTTPException(404, "Script not found")
    return None

@router.post("/{script_id}/run")
async def run_script_now(
    script_id: int,
    background_tasks: BackgroundTasks,
    current_user: UserModel = Depends(get_current_user),
    script_service: ScriptService = Depends(get_script_service)
):
    execution_id = await script_service.run_script_now(
        script_id, 
        current_user.id,
        background_tasks
    )
    return {"execution_id": execution_id, "message": "Script started"}

@router.get("/{script_id}/executions", response_model=List[ExecutionResponse])
async def get_script_executions(
    script_id: int,
    current_user: UserModel = Depends(get_current_user),
    script_service: ScriptService = Depends(get_script_service),
    limit: int = 50
):
    executions = await script_service.get_script_executions(script_id, current_user.id, limit)
    return executions
