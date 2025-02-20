"""Meeting scheduler module for handling calendar integrations and scheduling automation."""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import os
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from .config import get_config
from .models import Meeting, init_db

class MeetingScheduler:
    def __init__(self, db_url: str):
        """Initialize the meeting scheduler with calendar configurations."""
        self.config = get_config()
        self.db_engine = init_db(db_url)
        self.credentials = None
        self.calendar_service = None
        self.calendly_token = os.getenv('CALENDLY_API_TOKEN')
        self.calendly_user = os.getenv('CALENDLY_USER_URI')
        self._init_calendar_service()

    def _init_calendar_service(self) -> None:
        """Initialize Google Calendar service with OAuth2 credentials."""
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        if os.path.exists('token.json'):
            self.credentials = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.credentials = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(self.credentials.to_json())

        self.calendar_service = build('calendar', 'v3', credentials=self.credentials)

    def create_calendly_event(self, event_type_uri: str, email: str) -> Dict:
        """Create a Calendly event link.

        Args:
            event_type_uri (str): Calendly event type URI
            email (str): Invitee email

        Returns:
            Dict: Calendly event creation response
        """
        headers = {
            "Authorization": f"Bearer {self.calendly_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "event_type": event_type_uri,
            "invitee": {
                "email": email
            }
        }

        response = requests.post(
            f"https://api.calendly.com/scheduling_links",
            headers=headers,
            json=payload
        )

        if response.status_code == 201:
            data = response.json()
            with Session(self.db_engine) as session:
                meeting = Meeting(
                    title=data['resource']['event_type']['name'],
                    start_time=datetime.utcnow(),  # Will be updated when scheduled
                    end_time=datetime.utcnow(),    # Will be updated when scheduled
                    organizer_email=self.calendly_user,
                    attendee_email=email,
                    provider='calendly',
                    external_id=data['resource']['booking_url']
                )
                session.add(meeting)
                session.commit()
            return {"success": True, "booking_url": data['resource']['booking_url']}
        
        return {"success": False, "error": response.text}

    def schedule_meeting(self, title: str, start_time: str, duration_minutes: int = 30,
                        attendees: List[str] = None, use_calendly: bool = False) -> Dict:
        """Schedule a meeting using either Google Calendar or Calendly.

        Args:
            title (str): Meeting title
            start_time (str): Start time in ISO format
            duration_minutes (int): Meeting duration in minutes
            attendees (List[str]): List of attendee email addresses
            use_calendly (bool): Whether to use Calendly for scheduling

        Returns:
            Dict: Created event details
        """
        if use_calendly and attendees:
            return self.create_calendly_event(
                self.config['calendly']['default_event_type'],
                attendees[0]
            )

        if attendees is None:
            attendees = []

        event = {
            'summary': title,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': (datetime.fromisoformat(start_time) + 
                           timedelta(minutes=duration_minutes)).isoformat(),
                'timeZone': 'UTC',
            },
            'attendees': [{'email': email} for email in attendees],
            'reminders': {
                'useDefault': True
            }
        }

        try:
            result = self.calendar_service.events().insert(calendarId='primary', body=event).execute()
            
            with Session(self.db_engine) as session:
                meeting = Meeting(
                    title=title,
                    start_time=datetime.fromisoformat(start_time),
                    end_time=datetime.fromisoformat(start_time) + timedelta(minutes=duration_minutes),
                    organizer_email=self.credentials.id_token['email'],
                    attendee_email=attendees[0] if attendees else '',
                    provider='google_calendar',
                    external_id=result['id']
                )
                session.add(meeting)
                session.commit()
            
            return {"success": True, "event_id": result['id']}
        except Exception as e:
            return {"success": False, "error": str(e)}