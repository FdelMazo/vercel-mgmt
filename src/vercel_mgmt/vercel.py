import httpx
import asyncio
from typing import Optional


API_BASE = "https://api.vercel.com"


class Vercel:
    def __init__(self, bearer_token: str, team_id: Optional[str] = None):
        self.bearer_token = bearer_token
        self.team_id = team_id

    async def deployments(
        self,
        *,
        state: Optional[str] = None,
        target: Optional[str] = None,
    ):
        url = f"{API_BASE}/v6/deployments"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
        params = {
            "teamId": self.team_id,
            "state": state,
            "target": target,
            "limit": 100,
        }

        async with httpx.AsyncClient() as client:
            request = client.build_request("GET", url, headers=headers, params=params)
            print(f"REQUEST: {request.method} {request.url}")

            response = await client.send(request)
            json = response.json()
            print(f"RESPONSE: {response.status_code} {json}")

            return json["deployments"]

    async def cancel_deployments(
        self,
        deployment_ids: list[str],
    ):
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
        params = {
            "teamId": self.team_id,
        }

        responses = []
        async with httpx.AsyncClient() as client:
            requests = [
                client.build_request(
                    "PATCH",
                    f"{API_BASE}/v12/deployments/{deployment_id}/cancel",
                    headers=headers,
                    params=params,
                )
                for deployment_id in deployment_ids
            ]

            for request in requests:
                print(f"REQUEST: {request.method} {request.url}")

            responses.extend(
                await asyncio.gather(
                    *[client.send(request) for request in requests],
                    return_exceptions=True,
                )
            )

            for response in responses:
                print(f"RESPONSE: {response.status_code} {response.json()}")

        return all(r.status_code == 200 for r in responses)
