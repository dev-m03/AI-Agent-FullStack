import os
import json
import re
from dotenv import load_dotenv
from dateparser import parse as parse_date
import google.generativeai as genai

from calendar_utils import book_event, check_availability

load_dotenv()

# ======================================================
# Configure Gemini (official SDK)
# ======================================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ======================================================
# Dynamically select a working Gemini model
# ======================================================
def get_model():
    models = genai.list_models()
    for m in models:
        if "generateContent" in m.supported_generation_methods:
            # pick the FIRST supported text model
            return genai.GenerativeModel(m.name)
    raise RuntimeError("No Gemini model with generateContent found")

model = get_model()

# ======================================================
# Helper: safely extract JSON from model output
# ======================================================
def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in model response")
        return json.loads(match.group())

# ======================================================
# Main intent handler (called by FastAPI)
# ======================================================
def handle_intent(user_input: str) -> str:
    try:
        prompt = f"""
You are a backend system. Respond ONLY with valid JSON.

User message:
"{user_input}"

If the user wants to check calendar:
{{ "intent": "check" }}

If the user wants to book a meeting:
{{
  "intent": "book",
  "summary": "meeting title",
  "start_time": "natural language time",
  "end_time": "natural language time"
}}
"""

        response = model.generate_content(prompt)
        data = extract_json(response.text)

        # -------- CHECK CALENDAR --------
        if data.get("intent") == "check":
            events = check_availability()
            if not events:
                return "✅ You're free!"
            return "\n".join(
                f"• **{e.get('summary','No title')}** at "
                f"`{e['start'].get('dateTime', e['start'].get('date'))}`"
                for e in events
            )

        # -------- BOOK MEETING --------
        if data.get("intent") == "book":
            start = parse_date(data.get("start_time"))
            end = parse_date(data.get("end_time"))

            if not start or not end:
                return "❌ Could not understand the provided time."

            event = book_event(
                data.get("summary", "Meeting"),
                start.isoformat(),
                end.isoformat()
            )

            return (
                f"✅ Meeting booked!\n"
                f"🔗 [View in Calendar]({event['htmlLink']})"
            )

        return "❌ I couldn't understand your request."

    except Exception as e:
        print("❌ Backend error:", e)
        return f"❌ Backend error: {str(e)}"
