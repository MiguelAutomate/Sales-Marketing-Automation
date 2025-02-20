"""Configuration module for AI Sales Agent."""

from typing import Dict
from pathlib import Path

# Base configuration
BASE_CONFIG = {
    "model": {
        "provider": "ollama",  # Supported: ollama, openai, gemini, anthropic, mistral
        "name": "deepseek-r1:14b",
        "temperature": 0.7,
        "api_url": "http://localhost:8000",
        "api_key": "",  # Required for OpenAI, Anthropic, Mistral
        "organization_id": ""  # Optional for some providers
    },
    "email": {
        "tracking": {
            "enabled": True,
            "events": ["open", "click", "bounce", "spam_report"],
            "webhook_url": "http://your-domain/webhook/email-events"
        }
    },
    "calendar": {
        "check_availability": True,
        "min_notice_hours": 1,
        "default_meeting_duration": 30,
        "timezone": "UTC"
    },
    "crewai": {
        "agents": {
            "lead_generation": {
                "name": "Lead Generator",
                "role": "Lead Generation Specialist",
                "goal": "Identify and qualify high-value leads"
            },
            "email_automation": {
                "name": "Email Manager",
                "role": "Email Automation Specialist",
                "goal": "Handle email campaigns and follow-ups"
            },
            "crm": {
                "name": "CRM Manager",
                "role": "CRM Data Specialist",
                "goal": "Maintain accurate CRM records"
            }
        }
    },
    "temporal": {
        "namespace": "ai-sales-agent",
        "task_queue": "sales-workflow",
        "server_url": "localhost:7233"
    },
    "llama_index": {
        "index_path": str(Path(__file__).parent / "data" / "knowledge_base"),
        "chunk_size": 1024,
        "similarity_top_k": 5
    },
    "social_media": {
        "twitter": {
            "api_key": "",
            "api_secret": "",
            "access_token": "",
            "access_token_secret": ""
        },
        "linkedin": {
            "client_id": "",
            "client_secret": "",
            "access_token": ""
        },
        "instagram": {
            "client_id": "",
            "client_secret": "",
            "access_token": ""
        }
    },
    "marketing": {
        "google_ads": {
            "client_id": "",
            "client_secret": "",
            "developer_token": "",
            "refresh_token": ""
        },
        "facebook_ads": {
            "app_id": "",
            "app_secret": "",
            "access_token": "",
            "account_id": ""
        }
    },
    "analytics": {
        "database": {
            "type": "postgres",  # or "mongodb"
            "host": "localhost",
            "port": 5432,
            "name": "ai_sales_analytics",
            "user": "",
            "password": ""
        },
        "tracking": {
            "conversion_stages": ["lead", "outreach", "meeting", "deal"],
            "metrics": ["response_rate", "meeting_rate", "conversion_rate"]
        }
    }
}

def get_config() -> Dict:
    """Get the configuration dictionary.
    
    Returns:
        Dict: Configuration settings
    """
    return BASE_CONFIG