from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agent import handle_intent

app = FastAPI()

# Allow CORS for all origins (necessary for Streamlit frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model for POST /chat
class ChatInput(BaseModel):
    message: str

# Root route (optional)
@app.get("/")
def read_root():
    return {"message": "TailorTalk backend is running."}

# Core route for frontend to POST messages
@app.post("/chat")
def chat(user_input: ChatInput):
    try:
        response = handle_intent(user_input.message)  # This returns a string
        return {"output": response}  # ✅ Ensure it's wrapped in a dict with "output"
    except Exception as e:
        return {"output": f"❌ Error: {str(e)}"}
