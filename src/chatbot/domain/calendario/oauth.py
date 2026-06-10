"""Value objects de OAuth do Google."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class OAuthToken:
    """Token OAuth Google em texto claro (apenas em memória, nunca persistido cru).

    Persistência cifrada é responsabilidade do :class:`OAuthGoogleStore`.
    """

    access_token: str
    refresh_token: str | None = None
    expira_em: datetime | None = None
