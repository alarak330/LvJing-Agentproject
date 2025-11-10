from fastapi import FastAPI
from sqlalchemy import create_engine

app = FastAPI()

engine = create_engine("自己填数据库的具体信息")


with engine.connect() as conn:
    print(" 数据库连接成功")

@app.get("/")
async def home():
    return {"message": "数据库已连接"}


##这个只是单纯的连接数据库的逻辑，没有其他业务逻辑，之后的增删改查之类的我会写另外的接口