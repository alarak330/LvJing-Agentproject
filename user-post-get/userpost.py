from fastapi import FastAPI,APIRouter, BackgroundTasks,Form,Request
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import HTMLResponse
import uuid 
import asyncio
import httpx
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates=Jinja2Templates(directory="templates")
tasks={}
app = FastAPI()


@router.post("/create_task")
async def create_task(background_tasks: BackgroundTasks, query: str = Form(...), report_type: str = Form(...)):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "message":"任务已创建"}
    background_tasks.add_task(run_status,task_id,query)
    return templates.TemplateResponse("task_status.html", {"request": {}, "task_id": task_id})

async def run_status(task_id: str, query: str):
    try:
        tasks[task_id]["status"] = "in_progress"
        tasks[task_id]["message"] = "任务进行中"
        await asyncio.sleep(10)  # 模拟长时间运行的任务
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["message"] = f"任务完成，查询内容：{query}"
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["message"] = f"任务失败，错误信息：{str(e)}"

@router.get ("/{task_id}/status", response_class=HTMLResponse)
async def get_task(request: Request, task_id: str):
    task = tasks.get(task_id)
    if not task:
        return {"error": "任务未找到"}
    return templates.TemplateResponse("task_status.html", {"request": request, "task_id": task_id, "status": task["status"], "message": task["message"]})