"""AI Social Media Management module for automated posting and engagement tracking."""

from typing import Dict, List
from agencyswarm import Agency, Agent
from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from composio_langchain import Action, ComposioToolSet
from .config import get_config

class SocialMediaManager:
    def __init__(self):
        """Initialize the social media manager with necessary components."""
        self.config = get_config()
        self.llm = Ollama(model=self.config['model']['name'])
        self.composio_toolset = ComposioToolSet()
        self._init_templates()
        self._init_tools()
        self._init_agents()

    def _init_templates(self) -> None:
        """Initialize prompt templates for social media content."""
        self.post_template = PromptTemplate(
            input_variables=["topic", "platform", "tone", "hashtags"],
            template="""Create an engaging {platform} post about {topic} with a {tone} tone.
            Include these hashtags: {hashtags}
            The post should be platform-appropriate in length and style.
            Include emojis where appropriate and a strong call-to-action."""
        )

        self.engagement_template = PromptTemplate(
            input_variables=["comment", "platform", "brand_voice"],
            template="""Generate a {brand_voice} response to this {platform} comment:
            {comment}
            The response should be authentic, helpful, and align with our brand voice."""
        )

    def _init_tools(self) -> None:
        """Initialize tools for social media management."""
        self.social_tools = self.composio_toolset.get_tools(
            actions=[
                Action.TWITTER_POST,
                Action.TWITTER_TRACK_ENGAGEMENT,
                Action.LINKEDIN_POST,
                Action.LINKEDIN_TRACK_ENGAGEMENT,
                Action.INSTAGRAM_POST,
                Action.INSTAGRAM_TRACK_ENGAGEMENT
            ]
        )

    def post_to_platform(self, content: str, platform: str, media_urls: List[str] = None) -> Dict:
        """Post content to specified social media platform.

        Args:
            content (str): Post content
            platform (str): Target platform (twitter, linkedin, instagram)
            media_urls (List[str], optional): URLs of media to attach

        Returns:
            Dict: Post response with status and post ID
        """
        try:
            if platform.lower() == "twitter":
                action = Action.TWITTER_POST
            elif platform.lower() == "linkedin":
                action = Action.LINKEDIN_POST
            elif platform.lower() == "instagram":
                action = Action.INSTAGRAM_POST
            else:
                raise ValueError(f"Unsupported platform: {platform}")

            post_tool = self.composio_toolset.get_tool(action)
            response = post_tool.execute({
                "content": content,
                "media_urls": media_urls or []
            })

            return {
                "success": True,
                "post_id": response.get("id"),
                "platform": platform,
                "posted_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "platform": platform
            }

    def analyze_sentiment(self, comment: str) -> str:
        """Analyze sentiment of social media engagement.

        Args:
            comment (str): User comment to analyze

        Returns:
            str: Sentiment classification (positive, neutral, negative)
        """
        sentiment_template = PromptTemplate(
            input_variables=["comment"],
            template="""Analyze the sentiment of this social media comment and classify it as 'positive', 'neutral', or 'negative':
            {comment}
            Consider the tone, language, and context when making the classification."""
        )
        chain = LLMChain(llm=self.llm, prompt=sentiment_template)
        return chain.run(comment=comment).strip().lower()

    def auto_respond(self, comment: str, platform: str) -> Dict:
        """Generate and post automated response based on comment sentiment.

        Args:
            comment (str): User comment to respond to
            platform (str): Social media platform

        Returns:
            Dict: Response details including sentiment and posted response
        """
        # Analyze comment sentiment
        sentiment = self.analyze_sentiment(comment)

        # Adjust brand voice based on sentiment
        if sentiment == "positive":
            brand_voice = "enthusiastic"
        elif sentiment == "neutral":
            brand_voice = "helpful"
        else:
            brand_voice = "professional"

        # Generate appropriate response
        response_content = self.generate_response(
            comment=comment,
            platform=platform,
            brand_voice=brand_voice
        )

        # Post the response
        post_result = self.post_to_platform(
            content=response_content,
            platform=platform
        )

        return {
            "success": post_result["success"],
            "sentiment": sentiment,
            "response": response_content,
            "post_result": post_result
        }

    def _init_agents(self) -> None:
        """Initialize AgencySwarm agents for social media tasks."""
        self.content_creator = Agent(
            name=self.config['crewai']['agents']['social_media']['content_creator']['name'],
            role=self.config['crewai']['agents']['social_media']['content_creator']['role'],
            goal=self.config['crewai']['agents']['social_media']['content_creator']['goal'],
            backstory="I excel at crafting viral social media posts and engaging with audiences",
            llm=self.llm,
            tools=self.social_tools
        )

        self.engagement_manager = Agent(
            name=self.config['crewai']['agents']['social_media']['engagement_manager']['name'],
            role=self.config['crewai']['agents']['social_media']['engagement_manager']['role'],
            goal=self.config['crewai']['agents']['social_media']['engagement_manager']['goal'],
            backstory="I specialize in building community through meaningful social media interactions",
            llm=self.llm,
            tools=self.social_tools
        )

        # Create the agency with all agents
        self.agency = Agency(
            agents=[self.content_creator, self.engagement_manager],
            max_iterations=2
        )

    def create_social_post(self, topic: str, platform: str, hashtags: List[str], tone: str = "casual") -> str:
        """Generate platform-specific social media post.

        Args:
            topic (str): Post topic or theme
            platform (str): Target platform (e.g., Twitter, LinkedIn, Instagram)
            hashtags (List[str]): Relevant hashtags
            tone (str): Desired post tone

        Returns:
            str: Generated post content
        """
        chain = LLMChain(llm=self.llm, prompt=self.post_template)
        return chain.run(
            topic=topic,
            platform=platform,
            tone=tone,
            hashtags=" ".join(hashtags)
        )

    def generate_response(self, comment: str, platform: str, brand_voice: str = "friendly") -> str:
        """Generate response to social media engagement.

        Args:
            comment (str): User comment to respond to
            platform (str): Social media platform
            brand_voice (str): Desired brand voice for response

        Returns:
            str: Generated response
        """
        chain = LLMChain(llm=self.llm, prompt=self.engagement_template)
        return chain.run(
            comment=comment,
            platform=platform,
            brand_voice=brand_voice
        )

    def analyze_engagement(self, post_data: Dict) -> Dict:
        """Analyze social media post performance and engagement.

        Args:
            post_data (Dict): Post metrics and engagement data

        Returns:
            Dict: Engagement analysis and recommendations
        """
        tasks = [
            {
                "agent": self.engagement_manager,
                "task": f"Analyze performance metrics for social media post: {post_data.get('id', 'Unknown')}"
            },
            {
                "agent": self.engagement_manager,
                "task": "Generate engagement optimization recommendations based on performance analysis"
            }
        ]

        result = self.agency.execute_tasks(tasks)
        return {"analysis": result}