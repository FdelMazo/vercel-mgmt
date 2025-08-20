import httpx
from typing import Optional, Literal


API_BASE = "https://api.vercel.com/v6"


class Vercel:
    def __init__(self, bearer_token: str, team_id: Optional[str] = None):
        self.bearer_token = bearer_token
        self.team_id = team_id

    async def deployments(
        self,
        *,
        state: Optional[
            Literal["BUILDING", "ERROR", "INITIALIZING", "QUEUED", "READY", "CANCELED"]
        ] = None,
    ):
        url = f"{API_BASE}/deployments"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
        params = {
            "teamId": self.team_id,
            "state": state,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            json = response.json()
            return json["deployments"]
