"""AgencySwarm agents module for orchestrating sales automation tasks."""

from typing import Dict, List
from agencyswarm import Agency, Agent
from langchain.llms import Ollama
from llama_index import SimpleDirectoryReader, GPTVectorStoreIndex
from composio_langchain import Action, ComposioToolSet
from .config import get_config
from .email_automation import EmailAutomation
from .lead_generation import LeadGenerator
from .license_manager import LicenseManager

class SalesAgency:
    def __init__(self, user_id: str):
        """Initialize the sales agency with necessary components.

        Args:
            user_id (str): Unique identifier for the user
        """
        self.config = get_config()
        self.llm = Ollama(model=self.config['model']['name'])
        self.composio_toolset = ComposioToolSet()
        self.license_manager = LicenseManager()
        self.agent_factory = AgentFactory(self.llm)
        self.user_id = user_id
        self.sales_agent = None
        self.additional_agents = []
        self._init_tools()
        self._register_agents()
        self._init_agents()

    def _init_tools(self) -> None:
        """Initialize tools for email and calendar operations."""
        self.email_tools = self.composio_toolset.get_tools(
            actions=[
                Action.GMAIL_CREATE_EMAIL_DRAFT,
                Action.GMAIL_TRACK_EMAIL,
                Action.GOOGLECALENDAR_FIND_FREE_SLOTS,
                Action.GOOGLECALENDAR_CREATE_EVENT
            ]
        )

    def _register_agents(self) -> None:
        """Register available agent types with the factory."""
        # Register Lead Generation Agent (default)
        self.agent_factory.register_agent(
            'lead_generation',
            Agent,
            required_tools=None
        )

        # Register Email Automation Agent (premium)
        self.agent_factory.register_agent(
            'email_automation',
            Agent,
            required_tools=[
                Action.GMAIL_CREATE_EMAIL_DRAFT,
                Action.GMAIL_TRACK_EMAIL,
                Action.GOOGLECALENDAR_FIND_FREE_SLOTS,
                Action.GOOGLECALENDAR_CREATE_EVENT
            ]
        )

        # Register CRM Management Agent (premium)
        self.agent_factory.register_agent(
            'crm',
            Agent,
            required_tools=None
        )

    def _init_agents(self) -> None:
        """Initialize AgencySwarm agents based on user's license."""
        # Create default lead generation agent
        self.sales_agent = self.agent_factory.create_agent(
            self.user_id,
            'lead_generation',
            self.config['crewai']['agents']['lead_generation']
        )

        # Initialize additional agents if user has access
        if self.license_manager.check_access(self.user_id, 'email_automation'):
            email_agent = self.agent_factory.create_agent(
                self.user_id,
                'email_automation',
                self.config['crewai']['agents']['email_automation']
            )
            if email_agent:
                self.additional_agents.append(email_agent)

        if self.license_manager.check_access(self.user_id, 'crm'):
            crm_agent = self.agent_factory.create_agent(
                self.user_id,
                'crm',
                self.config['crewai']['agents']['crm']
            )
            if crm_agent:
                self.additional_agents.append(crm_agent)

        # Create agency with available agents
        self.agency = Agency(
            agents=[self.sales_agent] + self.additional_agents,
            max_iterations=3
        )

    def execute_sales_workflow(self, industry: str, company_size: str, job_titles: List[str]) -> Dict:
        """Execute sales workflow with available agents.

        Args:
            industry (str): Target industry
            company_size (str): Company size range
            job_titles (List[str]): Target job titles

        Returns:
            Dict: Workflow execution results
        """
        tasks = []

        # Lead generation task
        if self.sales_agent:
            tasks.append({
                "agent": self.sales_agent,
                "task": f"Find leads in {industry} with company size {company_size} targeting {', '.join(job_titles)}"
            })

        # Add tasks for additional agents
        for agent in self.additional_agents:
            if "Email" in agent.name:
                tasks.append({
                    "agent": agent,
                    "task": "Send personalized outreach emails to qualified leads"
                })
            elif "CRM" in agent.name:
                tasks.append({
                    "agent": agent,
                    "task": "Update CRM with latest lead information and interaction data"
                })

        result = self.agency.execute_tasks(tasks)
        return {"workflow_result": result}