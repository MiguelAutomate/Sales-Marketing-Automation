"""Core AI module for message generation and response classification."""

from typing import Dict, Optional
from langchain.llms import Ollama, OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import GoogleGenerativeAI
from langchain_anthropic import Anthropic
from langchain_mistralai import MistralAI
from .config import get_config

class AICore:
    def __init__(self):
        """Initialize the AI core with dynamic model selection."""
        config = get_config()
        self.llm = self._initialize_llm(config['model'])
        self._init_templates()

    def _initialize_llm(self, model_config: Dict) -> any:
        """Initialize the appropriate LLM based on provider.

        Args:
            model_config (Dict): Model configuration from config file

        Returns:
            any: Initialized LLM instance

        Raises:
            ValueError: If provider is not supported
        """
        provider = model_config.get('provider', 'ollama')
        
        if provider == 'ollama':
            return Ollama(
                model=model_config['name'],
                temperature=model_config['temperature'],
                api_url=model_config['api_url']
            )
        elif provider == 'openai':
            return OpenAI(
                model=model_config['name'],
                temperature=model_config['temperature']
            )
        elif provider == 'gemini':
            return GoogleGenerativeAI(
                model=model_config['name'],
                temperature=model_config.get('temperature', 0.7)
            )
        elif provider == 'anthropic':
            return Anthropic(
                model=model_config['name'],
                temperature=model_config.get('temperature', 0.7)
            )
        elif provider == 'mistral':
            return MistralAI(
                model=model_config['name'],
                temperature=model_config.get('temperature', 0.7),
                api_key=model_config.get('api_key')
            )
        else:
            raise ValueError(f'Unsupported model provider: {provider}')

    def _init_templates(self) -> None:
        """Initialize prompt templates for different message types."""
        self.outreach_template = PromptTemplate(
            input_variables=["lead_name", "company", "pain_point"],
            template="Hi {lead_name},\n\nI noticed {company} is facing {pain_point}. We specialize in helping businesses like yours automate and optimize their sales processes.\n\nI'd love to share how we've helped similar companies achieve significant improvements in their sales efficiency. Would you be open to a brief call to explore how we could help {company}?\n\nBest regards"
        )

        self.follow_up_template = PromptTemplate(
            input_variables=["lead_name", "previous_context"],
            template="Hi {lead_name}, I wanted to follow up on my previous message "
                     "regarding {previous_context}. Would you be interested in "
                     "learning more about how we can help?"
        )

    def generate_initial_message(self, lead_data: Dict[str, str]) -> str:
        """Generate personalized initial outreach message.

        Args:
            lead_data (Dict[str, str]): Dictionary containing lead information

        Returns:
            str: Generated message
        """
        chain = LLMChain(llm=self.llm, prompt=self.outreach_template)
        return chain.run(**lead_data)

    def generate_follow_up(self, lead_name: str, previous_context: str) -> str:
        """Generate follow-up message based on previous interaction.

        Args:
            lead_name (str): Name of the lead
            previous_context (str): Context from previous interaction

        Returns:
            str: Generated follow-up message
        """
        chain = LLMChain(llm=self.llm, prompt=self.follow_up_template)
        return chain.run(lead_name=lead_name, previous_context=previous_context)

    def classify_response(self, response_text: str) -> str:
        """Classify prospect's response into categories.

        Args:
            response_text (str): Prospect's response text

        Returns:
            str: Classification (positive, neutral, negative)
        """
        template = PromptTemplate(
            input_variables=["response"],
            template="Classify the following sales prospect response as either "
                     "'positive' (showing clear interest), 'neutral' (needs more "
                     "nurturing), or 'negative' (not interested):\n\n{response}"
        )
        chain = LLMChain(llm=self.llm, prompt=template)
        return chain.run(response=response_text).strip().lower()