"""Email processing and calendar integration module using CrewAI agents."""

from typing import Dict, Optional, List
from datetime import datetime
import re
from agencyswarm import Agency, Agent
from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from .config import get_config
from composio_langchain import Action, ComposioToolSet

class EmailProcessor:
    def __init__(self):
        """Initialize email processor with necessary components."""
        self.config = get_config()
        self.llm = Ollama(model=self.config['model']['name'])
        self.composio_toolset = ComposioToolSet()
        self._init_tools()
        self._init_agents()

    def _init_tools(self) -> None:
        """Initialize tools for calendar and email operations."""
        self.schedule_tools = self.composio_toolset.get_tools(
            actions=[
                Action.GOOGLECALENDAR_FIND_FREE_SLOTS,
                Action.GOOGLECALENDAR_CREATE_EVENT,
                Action.GMAIL_CREATE_EMAIL_DRAFT,
                Action.GMAIL_TRACK_EMAIL
            ]
        )
        self.email_tools = self.composio_toolset.get_tools(
            actions=[
                Action.GMAIL_CREATE_EMAIL_DRAFT,
                Action.GMAIL_TRACK_EMAIL
            ]
        )

    def _init_agents(self) -> None:
        """Initialize CrewAI agents for email and calendar management."""
        self.email_assistant = Agent(
            name="Email Assistant",
            role="Email Processing Specialist",
            goal="Process emails and manage calendar events efficiently",
            backstory="I am an AI agent specialized in analyzing emails and managing calendar events",
            llm=self.llm,
            tools=self.schedule_tools
        )
        
        self.agency = Agency(
            agents=[self.email_assistant],
            max_iterations=2
        )

    def extract_sender_email(self, payload: Dict) -> Optional[str]:
        """Extract sender's email from email headers.

        Args:
            payload (Dict): Email payload containing headers

        Returns:
            Optional[str]: Extracted email address or None
        """
        delivered_to_header_found = False
        for header in payload.get("headers", []):
            if header.get("name", "") == "Delivered-To" and header.get("value", "") != "":
                delivered_to_header_found = True
                break

        if not delivered_to_header_found:
            return None

        for header in payload.get("headers", []):
            if header.get("name") == "From":
                match = re.search(r"[\w\.-]+@[\w\.-]+", header.get("value", ""))
                if match:
                    return match.group(0)
        return None

    def process_email(self, payload: Dict) -> Dict:
        """Process incoming email and handle calendar events.

        Args:
            payload (Dict): Email payload containing message details

        Returns:
            Dict: Processing results
        """
        thread_id = payload.get("threadId")
        message = payload.get("messageText")
        sender_mail = payload.get("sender")

        if not sender_mail:
            return {"error": "No sender email found"}

        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timezone = datetime.now().astimezone().tzinfo

        # Define tasks for the agency
        tasks = [
            {
                "agent": self.email_assistant,
                "task": f"""1. Analyze the email content and decide if an event should be created. 
                    a. The email was received from {sender_mail} 
                    b. The content of the email is: {message} 
                    c. The thread id is: {thread_id}.
                2. If you decide to create an event, try to find a free slot 
                using Google Calendar Find Free Slots action.
                3. Once you find a free slot, use Google Calendar Create Event 
                action to create the event at a free slot and send the invite to {sender_mail}."""
            },
            {
                "agent": self.email_assistant,
                "task": f"""If an event was created, draft a confirmation email for the created event. 
                The receiver of the mail is: {sender_mail}, the subject should be meeting scheduled and body
                should describe what the meeting is about"""
            }
        ]

        try:
            result = self.agency.execute_tasks(tasks)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}