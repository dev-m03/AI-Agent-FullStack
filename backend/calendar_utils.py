import datetime
import os
import json
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Calendar API setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.getenv("CALENDAR_ID") or 'dev.m01113@gmail.com'  # fallback default

# ✅ Load credentials from base64 string stored in env var
b64_creds = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64")
if not b64_creds:
    raise EnvironmentError("❌ Missing GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 env variable.")

try:
    creds_dict = json.loads(base64.b64decode(b64_creds))
    credentials = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
except Exception as e:
    raise RuntimeError(f"❌ Failed to initialize Google Calendar API: {e}")

# ✅ Check upcoming events
def check_availability():
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

# ✅ Book a new calendar event
def book_event(summary, start_time, end_time):
    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Kolkata',
        },
    }
    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return created_event
