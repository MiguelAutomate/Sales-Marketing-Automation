"""License manager module for handling user access to different agent types."""

from typing import Dict, List, Set

class LicenseManager:
    def __init__(self):
        """Initialize the license manager with empty user licenses."""
        self.user_licenses: Dict[str, Set[str]] = {}
        self.default_agent = 'lead_generation'

    def initialize_user(self, user_id: str) -> None:
        """Initialize a new user with default agent access.

        Args:
            user_id (str): Unique identifier for the user
        """
        if user_id not in self.user_licenses:
            self.user_licenses[user_id] = {self.default_agent}

    def unlock_agent(self, user_id: str, agent_type: str) -> bool:
        """Grant access to a specific agent type for a user.

        Args:
            user_id (str): Unique identifier for the user
            agent_type (str): Type of agent to unlock

        Returns:
            bool: True if agent was successfully unlocked, False if already unlocked
        """
        self.initialize_user(user_id)
        
        if agent_type in self.user_licenses[user_id]:
            return False
            
        self.user_licenses[user_id].add(agent_type)
        return True

    def check_access(self, user_id: str, agent_type: str) -> bool:
        """Check if a user has access to a specific agent type.

        Args:
            user_id (str): Unique identifier for the user
            agent_type (str): Type of agent to check

        Returns:
            bool: True if user has access to the agent type
        """
        self.initialize_user(user_id)
        return agent_type in self.user_licenses[user_id]

    def get_unlocked_agents(self, user_id: str) -> List[str]:
        """Get list of agent types unlocked for a user.

        Args:
            user_id (str): Unique identifier for the user

        Returns:
            List[str]: List of unlocked agent types
        """
        self.initialize_user(user_id)
        return list(self.user_licenses[user_id])

    def revoke_access(self, user_id: str, agent_type: str) -> bool:
        """Revoke access to a specific agent type for a user.

        Args:
            user_id (str): Unique identifier for the user
            agent_type (str): Type of agent to revoke

        Returns:
            bool: True if access was revoked, False if user didn't have access
        """
        if user_id not in self.user_licenses:
            return False
            
        if agent_type == self.default_agent:
            return False  # Cannot revoke access to default agent
            
        if agent_type in self.user_licenses[user_id]:
            self.user_licenses[user_id].remove(agent_type)
            return True
            
        return False