"""Agent factory module for dynamic agent creation and registration."""

from typing import Dict, List, Optional, Type
from agencyswarm import Agent
from langchain.llms import BaseLLM
from composio_langchain import Action, ComposioToolSet

class AgentFactory:
    def __init__(self, llm: BaseLLM):
        """Initialize the agent factory.

        Args:
            llm (BaseLLM): Language model instance to use for agents
        """
        self.llm = llm
        self.registered_agents: Dict[str, Type[Agent]] = {}
        self.agent_tools: Dict[str, List[Action]] = {}
        self.default_agent_type = 'lead_generation'  # Set default single agent type
        self.agent_capabilities: Dict[str, List[str]] = {
            'lead_generation': [
                'find leads', 'identify prospects', 'sales prospecting',
                'lead qualification', 'market research', 'company research'
            ],
            'email_automation': [
                'send emails', 'email tracking', 'follow up', 'email campaign',
                'calendar', 'schedule', 'meeting', 'appointment'
            ],
            'crm': [
                'crm', 'customer data', 'contact management', 'deal tracking',
                'interaction history', 'pipeline management'
            ]
        }
        self.unlocked_agents: Dict[str, List[str]] = {}  # Track unlocked agents per user

    def register_agent(self, agent_type: str, agent_class: Type[Agent], required_tools: Optional[List[Action]] = None) -> None:
        """Register a new agent type.

        Args:
            agent_type (str): Unique identifier for the agent type
            agent_class (Type[Agent]): Agent class to register
            required_tools (Optional[List[Action]]): List of required tools for the agent
        """
        self.registered_agents[agent_type] = agent_class
        if required_tools:
            self.agent_tools[agent_type] = required_tools

    def unlock_agent(self, user_id: str, agent_type: str) -> bool:
        """Unlock additional agent type for a user.

        Args:
            user_id (str): Unique identifier for the user
            agent_type (str): Type of agent to unlock

        Returns:
            bool: True if agent was successfully unlocked
        """
        if user_id not in self.unlocked_agents:
            self.unlocked_agents[user_id] = [self.default_agent_type]
        
        if agent_type not in self.unlocked_agents[user_id]:
            self.unlocked_agents[user_id].append(agent_type)
            return True
        return False

    def create_agent(self, user_id: str, agent_type: str, config: Dict) -> Optional[Agent]:
        """Create an agent instance if user has access.

        Args:
            user_id (str): Unique identifier for the user
            agent_type (str): Type of agent to create
            config (Dict): Agent configuration

        Returns:
            Optional[Agent]: Created agent instance or None if unauthorized

        Raises:
            ValueError: If agent type is not registered
        """
        # Initialize user's unlocked agents if not exists
        if user_id not in self.unlocked_agents:
            self.unlocked_agents[user_id] = [self.default_agent_type]

        # Check if user has access to this agent type
        if agent_type not in self.unlocked_agents[user_id]:
            return None

        if agent_type not in self.registered_agents:
            raise ValueError(f"Agent type '{agent_type}' not registered")

        agent_tools = None
        if agent_type in self.agent_tools:
            toolset = ComposioToolSet()
            agent_tools = toolset.get_tools(actions=self.agent_tools[agent_type])

        return self.registered_agents[agent_type](
            name=config['name'],
            role=config['role'],
            goal=config['goal'],
            backstory=config.get('backstory', ''),
            llm=self.llm,
            tools=agent_tools
        )

    def get_relevant_agents(self, user_id: str, prompt: str, min_score: float = 0.1) -> List[str]:
        """Determine relevant agents based on prompt analysis and user access.

        Args:
            user_id (str): Unique identifier for the user
            prompt (str): User's input prompt
            min_score (float): Minimum relevance score threshold (0-1)

        Returns:
            List[str]: List of relevant agent types user has access to
        """
        relevant_agents = []
        prompt = prompt.lower()

        # Get user's unlocked agents, defaulting to lead_generation
        available_agents = self.unlocked_agents.get(user_id, [self.default_agent_type])

        for agent_type, capabilities in self.agent_capabilities.items():
            # Only consider agents the user has unlocked
            if agent_type not in available_agents:
                continue

            matches = sum(keyword in prompt for keyword in capabilities)
            if matches > 0:
                score = matches / len(capabilities)
                if score >= min_score:
                    relevant_agents.append((agent_type, score))

        relevant_agents.sort(key=lambda x: x[1], reverse=True)
        return [agent_type for agent_type, _ in relevant_agents]

    def create_agents_from_config(self, user_id: str, agents_config: Dict[str, Dict], prompt: str = None) -> List[Agent]:
        """Create multiple agents from configuration based on user access.

        Args:
            user_id (str): Unique identifier for the user
            agents_config (Dict[str, Dict]): Configuration for multiple agents
            prompt (str, optional): User prompt for smart agent selection

        Returns:
            List[Agent]: List of created agent instances user has access to
        """
        agents = []
        
        if prompt:
            relevant_agent_types = self.get_relevant_agents(user_id, prompt)
            agent_configs = {agent_type: agents_config[agent_type] 
                           for agent_type in relevant_agent_types 
                           if agent_type in agents_config}
        else:
            # Only include agents the user has unlocked
            available_agents = self.unlocked_agents.get(user_id, [self.default_agent_type])
            agent_configs = {agent_type: agents_config[agent_type]
                           for agent_type in available_agents
                           if agent_type in agents_config}

        for agent_type, config in agent_configs.items():
            try:
                agent = self.create_agent(user_id, agent_type, config)
                if agent:  # Only append if agent was successfully created
                    agents.append(agent)
            except ValueError as e:
                print(f"Warning: {str(e)}")
        return agents