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

model = genai.GenerativeModel("gemini-1.5-flash")

# ======================================================
# Helper: safely extract JSON from LLM output
# ======================================================
def extract_json(text: str) -> dict:
    """
    Extract the first JSON object from text.
    Works even if Gemini adds extra text.
    """
    try:
        # Direct JSON
        return json.loads(text)
    except:
        # Try extracting JSON block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in LLM response")
        return json.loads(match.group())

# ======================================================
# Main intent handler
# ======================================================
def handle_intent(user_input: str) -> str:
    try:
        prompt = f"""
You are a backend system. You MUST respond in valid JSON only.

User message:
"{user_input}"

Rules:
- NO markdown
- NO explanation
- ONLY JSON

If user wants to check calendar:
{{ "intent": "check" }}

If user wants to book a meeting:
{{
  "intent": "book",
  "summary": "meeting title",
  "start_time": "natural language time",
  "end_time": "natural language time"
}}
"""

        response = model.generate_content(prompt)
        data = extract_json(response.text)

        # ---------------- CHECK CALENDAR ----------------
        if data.get("intent") == "check":
            events = check_availability()
            if not events:
                return "✅ You're free!"

            return "\n".join(
                f"• **{e.get('summary','No title')}** at "
                f"`{e['start'].get('dateTime', e['start'].get('date'))}`"
                for e in events
            )

        # ---------------- BOOK MEETING ----------------
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

        return "❌ I couldn’t understand your request."

    except Exception as e:
        print("❌ Backend error:", e)
        return "❌ Something went wrong. Please try again."
