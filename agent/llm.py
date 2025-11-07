from langchain_openai import ChatOpenAI
import dotenv
import os

def getchatmodel():
    dotenv.load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("DEEPSEEK_API_KEY")
    os.environ["OPENAI_BASE_URL"] = os.getenv("DEEPSEEK_BASE_URL")
    model = ChatOpenAI(
        model="deepseek-chat"
    )
    return model

def getreasonmodel():
    dotenv.load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("DEEPSEEK_API_KEY")
    os.environ["OPENAI_BASE_URL"] = os.getenv("DEEPSEEK_BASE_URL")
    model = ChatOpenAI(
        model="deepseek-reason"
    )
    return model