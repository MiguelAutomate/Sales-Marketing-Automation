"""Email automation module for handling outbound communication and follow-ups."""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, TrackingSettings, ClickTracking, OpenTracking
from flask import Flask, request, jsonify
from sqlalchemy.orm import Session
from .models import EmailEvent, init_db

class EmailAutomation:
    def __init__(self, sendgrid_api_key: str, from_email: str, db_url: str, webhook_auth_token: str = None):
        """Initialize email automation with SendGrid and database configuration.

        Args:
            sendgrid_api_key (str): SendGrid API key
            from_email (str): Sender email address
            db_url (str): Database connection URL
            webhook_auth_token (str): Authentication token for webhook validation
        """
        self.sg_client = SendGridAPIClient(sendgrid_api_key)
        self.from_email = from_email
        self.webhook_auth_token = webhook_auth_token
        self.db_engine = init_db(db_url)
        self.app = Flask(__name__)
        self._setup_webhook_endpoints()

    def _setup_webhook_endpoints(self) -> None:
        """Set up Flask endpoints for SendGrid event webhooks."""
        @self.app.route('/sendgrid/events', methods=['POST'])
        def handle_sendgrid_event():
            if self.webhook_auth_token:
                auth_header = request.headers.get('Authorization')
                if not auth_header or auth_header != f'Bearer {self.webhook_auth_token}':
                    return jsonify({'error': 'Unauthorized'}), 401

            events = request.get_json()
            for event in events:
                self._process_email_event(event)
            return jsonify({'status': 'success'}), 200

    def _process_email_event(self, event: Dict) -> None:
        """Process and store incoming SendGrid event data.

        Args:
            event (Dict): SendGrid event data
        """
        event_type = event.get('event')
        email = event.get('email')
        timestamp = datetime.fromtimestamp(event.get('timestamp', datetime.utcnow().timestamp()))
        
        if event_type in ['open', 'click', 'bounce', 'spam_report', 'unsubscribe']:
            with Session(self.db_engine) as session:
                email_event = EmailEvent(
                    email=email,
                    event_type=event_type,
                    timestamp=timestamp,
                    metadata=str(event)  # Store full event data as JSON string
                )
                session.add(email_event)
                session.commit()

    def send_email(self, to_email: str, subject: str, content: str) -> Dict:
        """Send an email using SendGrid with tracking enabled.

        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            content (str): Email content (HTML)

        Returns:
            Dict: SendGrid response
        """
        message = Mail(
            from_email=Email(self.from_email),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", content)
        )

        # Enable email tracking
        tracking_settings = TrackingSettings()
        tracking_settings.click_tracking = ClickTracking(enable=True, enable_text=True)
        tracking_settings.open_tracking = OpenTracking(enable=True)
        message.tracking_settings = tracking_settings

        try:
            response = self.sg_client.send(message)
            return {
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 300,
                "sent_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status_code": 500,
                "success": False,
                "error": str(e)
            }

    def schedule_follow_up(self, lead_data: Dict, days_delay: int = 3) -> Dict:
        """Schedule a follow-up email.

        Args:
            lead_data (Dict): Lead information
            days_delay (int): Days to wait before sending follow-up

        Returns:
            Dict: Scheduled email information
        """
        send_at = datetime.utcnow() + timedelta(days=days_delay)
        
        # Format for SendGrid's scheduled sends
        message = Mail(
            from_email=Email(self.from_email),
            to_emails=To(lead_data["email"]),
            subject=f"Following up on our previous conversation",
            html_content=Content("text/html", lead_data["follow_up_content"])
        )
        message.send_at = int(send_at.timestamp())

        try:
            response = self.sg_client.send(message)
            return {
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 300,
                "scheduled_for": send_at.isoformat()
            }
        except Exception as e:
            return {
                "status_code": 500,
                "success": False,
                "error": str(e)
            }

    def create_email_template(self, template_name: str, content: str) -> Dict:
        """Create a new email template in SendGrid.

        Args:
            template_name (str): Name of the template
            content (str): HTML content of the template

        Returns:
            Dict: Template creation response
        """
        try:
            response = self.sg_client.client.templates.post(
                request_body={
                    "name": template_name,
                    "generation": "dynamic",
                    "versions": [{
                        "name": "v1",
                        "subject": "{{subject}}",
                        "html_content": content,
                        "active": 1
                    }]
                }
            )
            return {
                "template_id": response.get("id"),
                "success": True,
                "created_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    def create_ab_test_campaign(self, subject_lines: List[str], content_variations: List[str], 
                             test_size: int = 1000, test_duration_hours: int = 24) -> Dict:
        """Create an A/B test email campaign.

        Args:
            subject_lines (List[str]): List of subject line variations to test
            content_variations (List[str]): List of email content variations
            test_size (int): Number of recipients for the test
            test_duration_hours (int): Duration of the test in hours

        Returns:
            Dict: A/B test campaign details
        """
        try:
            # Create A/B test campaign
            campaign_data = {
                "title": f"A/B Test Campaign - {datetime.utcnow().isoformat()}",
                "subject_line_variations": subject_lines,
                "content_variations": content_variations,
                "test_size": test_size,
                "test_duration": test_duration_hours,
                "start_time": datetime.utcnow().isoformat()
            }

            response = self.sg_client.client.campaigns.post(
                request_body=campaign_data
            )

            return {
                "campaign_id": response.get("id"),
                "success": True,
                "test_end_time": (datetime.utcnow() + timedelta(hours=test_duration_hours)).isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def analyze_ab_test_results(self, campaign_id: str) -> Dict:
        """Analyze the results of an A/B test campaign.

        Args:
            campaign_id (str): ID of the A/B test campaign

        Returns:
            Dict: Analysis results including winning variation
        """
        try:
            response = self.sg_client.client.campaigns._(campaign_id).stats.get()
            
            # Calculate metrics for each variation
            variations_metrics = []
            for variation in response.get("variations", []):
                metrics = {
                    "variation_id": variation["id"],
                    "opens": variation["opens"],
                    "clicks": variation["clicks"],
                    "open_rate": variation["open_rate"],
                    "click_rate": variation["click_rate"]
                }
                variations_metrics.append(metrics)

            # Determine winning variation
            winning_variation = max(variations_metrics, 
                                 key=lambda x: (x["open_rate"] + x["click_rate"]) / 2)

            return {
                "success": True,
                "variations_metrics": variations_metrics,
                "winning_variation": winning_variation,
                "analyzed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def create_personalized_followup(self, lead_data: Dict, engagement_history: List[Dict]) -> Dict:
        """Create a personalized follow-up based on previous engagement.

        Args:
            lead_data (Dict): Lead information
            engagement_history (List[Dict]): Previous engagement events

        Returns:
            Dict: Personalized follow-up details
        """
        # Analyze engagement patterns
        engagement_metrics = {
            "total_opens": sum(1 for e in engagement_history if e["event_type"] == "open"),
            "total_clicks": sum(1 for e in engagement_history if e["event_type"] == "click"),
            "last_interaction": max((e["timestamp"] for e in engagement_history), default=None)
        }

        # Determine follow-up strategy based on engagement
        if engagement_metrics["total_clicks"] > 0:
            follow_up_type = "high_engagement"
            days_delay = 1
        elif engagement_metrics["total_opens"] > 0:
            follow_up_type = "medium_engagement"
            days_delay = 2
        else:
            follow_up_type = "no_engagement"
            days_delay = 4

        # Generate personalized content based on engagement level
        template_data = {
            "lead_name": lead_data.get("name"),
            "company": lead_data.get("company"),
            "engagement_level": follow_up_type,
            "last_interaction": engagement_metrics["last_interaction"]
        }

        try:
            # Get appropriate template for engagement level
            template_response = self.sg_client.client.templates.get(
                query_params={"generation": "dynamic", "name": f"followup_{follow_up_type}"}
            )

            # Schedule personalized follow-up
            return self.schedule_follow_up(
                lead_data={
                    "email": lead_data["email"],
                    "follow_up_content": template_response["versions"][0]["html_content"]
                },
                days_delay=days_delay
            )
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }