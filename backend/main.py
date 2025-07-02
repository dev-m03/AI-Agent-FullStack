from fastapi import FastAPI
from pydantic import BaseModel
from agent import handle_intent

app = FastAPI()

class UserMessage(BaseModel):
    message: str

@app.post("/chat")
def chat(user_input: UserMessage):
    reply = handle_intent(user_input.message)
    return {"response": reply}
