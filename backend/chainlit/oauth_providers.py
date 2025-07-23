import os
from typing import Dict, List, Optional, Tuple

from chainlit.user import User


class OAuthProvider:
    id: str
    env: List[str]
    client_id: str
    client_secret: str
    authorize_url: str
    authorize_params: Dict[str, str]
    default_prompt: Optional[str] = None

    async def get_token(self, code: str, url: str) -> str:
        raise NotImplementedError

    async def get_user_info(self, token: str) -> Tuple[Dict[str, str], User]:
        raise NotImplementedError

    def get_env_prefix(self) -> str:
        """Return environment prefix, like AZURE_AD."""

        return self.id.replace("-", "_").upper()

    def get_prompt(self) -> Optional[str]:
        """Return OAuth prompt param."""
        if prompt := os.environ.get(f"OAUTH_{self.get_env_prefix()}_PROMPT"):
            return prompt

        if prompt := os.environ.get("OAUTH_PROMPT"):
            return prompt

        return self.default_prompt


providers: list[OAuthProvider] = []


def get_oauth_provider(provider: str) -> Optional[OAuthProvider]:
    for p in providers:
        if p.id == provider:
            return p
    return None


def get_configured_oauth_providers():
    return [p.id for p in providers]
