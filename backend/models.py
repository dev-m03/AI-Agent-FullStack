from pydantic import BaseModel

class UserMessage(BaseModel):
    message: str
