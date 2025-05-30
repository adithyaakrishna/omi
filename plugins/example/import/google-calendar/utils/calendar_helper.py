from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def build_calendar_service(credentials_dict):
    """Build and return a Google Calendar service object"""
    credentials = Credentials(**credentials_dict)
    return build('calendar', 'v3', credentials=credentials)

def get_calendar_events(service, days=30):
    """Fetch calendar events for the specified number of days"""
    now = datetime.utcnow()
    start_time = (now - timedelta(days=days)).isoformat() + 'Z'
    end_time = now.isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_time,
        timeMax=end_time,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])

def format_event_memory(event):
    """Format a calendar event into a memory string"""
    start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
    end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))
    summary = event.get('summary', 'Untitled Event')
    description = event.get('description', '')
    location = event.get('location', '')
    
    memory_text = f"Calendar Event: {summary}"
    if description:
        memory_text += f". Notes: {description}"
    if location:
        memory_text += f". Location: {location}"
    memory_text += f". Time: {start} to {end}"
    
    return memory_text
