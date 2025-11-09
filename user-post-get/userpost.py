from fastapi import FastAPI, File
from pydantic import BaseModel


app = FastAPI()


class UserQuery(BaseModel):
    Event: str


@app.post("/ask")
async def user_ask(request: UserQuery):
    user_input = request.Event
    return {
        "message": "语句已接收！",
        "user_query": user_input,
        "next_step": "准备调用智能体处理请求"
    }

@app.post("/upload")
async def upload_file(file: bytes = File(...)):
    return {
        "file_size": len(file),
        "message": "文件已经被接收"
    }
