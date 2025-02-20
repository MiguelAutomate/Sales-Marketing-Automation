"""AI Marketing Assistant module for content creation and campaign management."""

from typing import Dict, List
from agencyswarm import Agency, Agent
from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from composio_langchain import Action, ComposioToolSet
from .config import get_config
from .license_manager import LicenseManager

class MarketingAssistant:
    def __init__(self, user_id: str):
        """Initialize the marketing assistant with necessary components.

        Args:
            user_id (str): Unique identifier for the user
        """
        self.config = get_config()
        self.llm = Ollama(model=self.config['model']['name'])
        self.composio_toolset = ComposioToolSet()
        self.license_manager = LicenseManager()
        self.user_id = user_id
        self._init_templates()
        self._init_tools()
        self._init_agents()

    def _init_templates(self) -> None:
        """Initialize prompt templates for content generation."""
        self.content_template = PromptTemplate(
            input_variables=["topic", "platform", "tone"],
            template="""Create engaging {platform} content about {topic} with a {tone} tone.
            The content should be informative, engaging, and aligned with our brand voice.
            Include relevant hashtags and call-to-actions where appropriate."""
        )

        self.campaign_template = PromptTemplate(
            input_variables=["target_audience", "objective", "budget"],
            template="""Design a marketing campaign for {target_audience} with the objective of {objective}.
            Consider the budget of ${budget} and suggest optimal channel allocation and timing."""
        )

    def _init_tools(self) -> None:
        """Initialize tools for content and campaign management."""
        self.marketing_tools = self.composio_toolset.get_tools(
            actions=[
                Action.GMAIL_CREATE_EMAIL_DRAFT,
                Action.GMAIL_TRACK_EMAIL
            ]
        )

    def _init_agents(self) -> None:
        """Initialize AgencySwarm agents based on user's license."""
        # Create content creator agent (default)
        self.content_creator = Agent(
            name=self.config['crewai']['agents']['content_creation']['name'],
            role=self.config['crewai']['agents']['content_creation']['role'],
            goal=self.config['crewai']['agents']['content_creation']['goal'],
            backstory="I specialize in crafting compelling marketing messages across different platforms",
            llm=self.llm,
            tools=self.marketing_tools
        )

        # Initialize campaign manager if user has access
        self.campaign_manager = None
        if self.license_manager.check_access(self.user_id, 'campaign_management'):
            self.campaign_manager = Agent(
                name=self.config['crewai']['agents']['campaign_management']['name'],
                role=self.config['crewai']['agents']['campaign_management']['role'],
                goal=self.config['crewai']['agents']['campaign_management']['goal'],
                backstory="I excel at planning and executing successful marketing campaigns",
                llm=self.llm,
                tools=self.marketing_tools
            )

        # Create the agency with available agents
        agents = [self.content_creator]  # Always include default agent
        if self.campaign_manager:
            agents.append(self.campaign_manager)

        self.agency = Agency(
            agents=agents,
            max_iterations=2
        )

    def generate_content(self, topic: str, platform: str, tone: str = "professional") -> str:
        """Generate platform-specific marketing content.

        Args:
            topic (str): Content topic or theme
            platform (str): Target platform (e.g., blog, social media)
            tone (str): Desired content tone

        Returns:
            str: Generated content
        """
        chain = LLMChain(llm=self.llm, prompt=self.content_template)
        return chain.run(topic=topic, platform=platform, tone=tone)

    def create_campaign_plan(self, target_audience: str, objective: str, budget: float) -> Dict:
        """Create a comprehensive marketing campaign plan.

        Args:
            target_audience (str): Target audience description
            objective (str): Campaign objective
            budget (float): Available budget

        Returns:
            Dict: Campaign plan details
        """
        if not self.campaign_manager:
            return {"error": "Campaign management requires premium access"}
            
        chain = LLMChain(llm=self.llm, prompt=self.campaign_template)
        plan = chain.run(
            target_audience=target_audience,
            objective=objective,
            budget=budget
        )
        return {"campaign_plan": plan}

    def analyze_performance(self, campaign_data: Dict) -> Dict:
        """Analyze marketing campaign performance.

        Args:
            campaign_data (Dict): Campaign metrics and data

        Returns:
            Dict: Performance analysis and recommendations
        """
        if not self.campaign_manager:
            return {"error": "Campaign analysis requires premium access"}
            
        tasks = [
            {
                "agent": self.campaign_manager,
                "task": f"Analyze performance metrics for campaign: {campaign_data.get('name', 'Unknown')}"
            },
            {
                "agent": self.campaign_manager,
                "task": "Generate optimization recommendations based on performance analysis"
            }
        ]

        result = self.agency.execute_tasks(tasks)
        return {"analysis": result}