from fastapi import FastAPI, APIRouter, BackgroundTasks, Form, Request
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid
import asyncio
import httpx
from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test():
    return {"message": "Router working!"}

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


app.include_router(router, prefix="/report")
app.include_router(router, prefix="/upload")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
