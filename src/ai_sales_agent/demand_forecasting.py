"""Demand Forecasting and Pricing Optimization module for sales and inventory management."""

from typing import Dict, List
from datetime import datetime, timedelta
from agencyswarm import Agency, Agent
from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from composio_langchain import Action, ComposioToolSet
from .config import get_config

class DemandForecaster:
    def __init__(self):
        """Initialize the demand forecasting system with necessary components."""
        self.config = get_config()
        self.llm = Ollama(model=self.config['model']['name'])
        self.composio_toolset = ComposioToolSet()
        self._init_templates()
        self._init_tools()
        self._init_agents()

    def _init_templates(self) -> None:
        """Initialize prompt templates for forecasting and pricing analysis."""
        self.forecast_template = PromptTemplate(
            input_variables=["historical_data", "timeframe", "product_category"],
            template="""Analyze historical sales data for {product_category} over the past {timeframe}:
            {historical_data}
            Provide demand forecasts, identify trends, and suggest inventory levels."""
        )

        self.pricing_template = PromptTemplate(
            input_variables=["product_data", "competitor_prices", "market_conditions"],
            template="""Optimize pricing strategy based on:
            Product Data: {product_data}
            Competitor Prices: {competitor_prices}
            Market Conditions: {market_conditions}
            Suggest optimal price points and promotional timing."""
        )

    def _init_tools(self) -> None:
        """Initialize tools for data analysis and market monitoring."""
        self.analysis_tools = self.composio_toolset.get_tools(
            actions=[
                Action.GMAIL_CREATE_EMAIL_DRAFT,
                Action.GMAIL_TRACK_EMAIL
            ]
        )

    def _init_agents(self) -> None:
        """Initialize AgencySwarm agents for forecasting and pricing tasks."""
        self.demand_analyst = Agent(
            name="Demand Analyst",
            role="Demand Forecasting Specialist",
            goal="Accurately predict demand patterns and optimize inventory levels",
            backstory="I specialize in analyzing sales data and forecasting future demand",
            llm=self.llm,
            tools=self.analysis_tools
        )

        self.pricing_strategist = Agent(
            name="Pricing Strategist",
            role="Pricing Optimization Specialist",
            goal="Determine optimal pricing strategies to maximize revenue",
            backstory="I excel at analyzing market conditions and setting competitive prices",
            llm=self.llm,
            tools=self.analysis_tools
        )

        # Create the agency with all agents
        self.agency = Agency(
            agents=[self.demand_analyst, self.pricing_strategist],
            max_iterations=2
        )

    def generate_demand_forecast(self, historical_data: Dict, timeframe: str, 
                               product_category: str) -> Dict:
        """Generate demand forecasts based on historical data.

        Args:
            historical_data (Dict): Historical sales and inventory data
            timeframe (str): Forecast timeframe (e.g., '3 months', '1 year')
            product_category (str): Product category to analyze

        Returns:
            Dict: Demand forecasts and recommendations
        """
        chain = LLMChain(llm=self.llm, prompt=self.forecast_template)
        forecast = chain.run(
            historical_data=historical_data,
            timeframe=timeframe,
            product_category=product_category
        )
        return {"forecast": forecast}

    def optimize_pricing(self, product_data: Dict, competitor_prices: List[float], 
                        market_conditions: Dict) -> Dict:
        """Optimize pricing strategy based on market data.

        Args:
            product_data (Dict): Product details and costs
            competitor_prices (List[float]): List of competitor prices
            market_conditions (Dict): Current market conditions

        Returns:
            Dict: Pricing recommendations and strategy
        """
        chain = LLMChain(llm=self.llm, prompt=self.pricing_template)
        strategy = chain.run(
            product_data=product_data,
            competitor_prices=competitor_prices,
            market_conditions=market_conditions
        )
        return {"pricing_strategy": strategy}

    def analyze_market_trends(self, market_data: Dict) -> Dict:
        """Analyze market trends and generate insights.

        Args:
            market_data (Dict): Market analysis data

        Returns:
            Dict: Market analysis and recommendations
        """
        tasks = [
            {
                "agent": self.demand_analyst,
                "task": "Analyze current market trends and demand patterns"
            },
            {
                "agent": self.pricing_strategist,
                "task": "Generate pricing recommendations based on market analysis"
            }
        ]

        result = self.agency.execute_tasks(tasks)
        return {"analysis": result}