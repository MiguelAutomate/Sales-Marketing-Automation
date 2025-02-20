"""Lead generation module for scraping and enriching prospect data."""

from typing import Dict, List, Optional
import requests
from datetime import datetime

class LeadGenerator:
    def __init__(
        self,
        apollo_api_key: str,
        clearbit_api_key: Optional[str] = None
    ):
        """Initialize lead generation with API configurations.

        Args:
            apollo_api_key (str): Apollo.io API key
            clearbit_api_key (Optional[str]): Clearbit API key for data enrichment
        """
        self.apollo_api_key = apollo_api_key
        self.clearbit_api_key = clearbit_api_key
        self.apollo_base_url = "https://api.apollo.io/v1"

    def search_leads(
        self,
        industry: str,
        company_size: str,
        job_titles: List[str],
        limit: int = 100
    ) -> List[Dict]:
        """Search for leads matching specified criteria using Apollo.io.

        Args:
            industry (str): Target industry
            company_size (str): Company size range (e.g., '11-50')
            job_titles (List[str]): List of target job titles
            limit (int): Maximum number of leads to return

        Returns:
            List[Dict]: List of lead data dictionaries
        """
        url = f"{self.apollo_base_url}/mixed_people/search"
        headers = {"Authorization": f"Bearer {self.apollo_api_key}"}
        
        params = {
            "q_organization_industry_text": industry,
            "q_organization_company_size": company_size,
            "q_titles": job_titles,
            "page": 1,
            "per_page": min(limit, 100)
        }

        try:
            response = requests.post(url, headers=headers, json=params)
            response.raise_for_status()
            return response.json().get("people", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching leads from Apollo: {e}")
            return []

    def enrich_lead(self, email: str) -> Dict:
        """Enrich lead data using Clearbit API.

        Args:
            email (str): Lead's email address

        Returns:
            Dict: Enriched lead data
        """
        if not self.clearbit_api_key:
            return {}

        url = f"https://person.clearbit.com/v2/people/find?email={email}"
        headers = {"Authorization": f"Bearer {self.clearbit_api_key}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error enriching lead data: {e}")
            return {}

    def format_lead_data(self, lead: Dict) -> Dict:
        """Format raw lead data into a standardized structure.

        Args:
            lead (Dict): Raw lead data

        Returns:
            Dict: Formatted lead data
        """
        return {
            "id": lead.get("id"),
            "first_name": lead.get("first_name"),
            "last_name": lead.get("last_name"),
            "email": lead.get("email"),
            "company": lead.get("organization", {}).get("name"),
            "title": lead.get("title"),
            "linkedin_url": lead.get("linkedin_url"),
            "company_size": lead.get("organization", {}).get("size"),
            "industry": lead.get("organization", {}).get("industry"),
            "created_at": datetime.utcnow().isoformat()
        }