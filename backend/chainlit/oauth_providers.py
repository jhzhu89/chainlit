from typing import Dict, Optional, Tuple

from chainlit.user import User


class OAuthProvider:
    id: str
    client_id: str
    authorize_url: str
    authorize_params: Dict[str, str]

    async def get_token(self, code: str, url: str) -> str:
        raise NotImplementedError

    async def get_user_info(self, token: str) -> Tuple[Dict[str, str], User]:
        raise NotImplementedError


providers: list[OAuthProvider] = []


def get_oauth_provider(provider: str) -> Optional[OAuthProvider]:
    for p in providers:
        if p.id == provider:
            return p
    return None


def get_configured_oauth_providers():
    return [p.id for p in providers]
