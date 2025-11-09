from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="智能体分析主程序")


class UserQuery(BaseModel):
    Event: str 


@app.post("/ask")
async def user_ask(request: UserQuery):
    user_input = request.Event
    return {
        "message": "语句已接收！",
        "user_query": user_input,
        "next_step": "准备调用数据分析智能体处理请求"
    }
