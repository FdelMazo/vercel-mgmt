import httpx
import asyncio
from typing import Optional
import webbrowser


API_BASE = "https://api.vercel.com"
TIMEOUT = httpx.Timeout(5.0)


class Vercel:
    def __init__(self, bearer_token: str, team_id: Optional[str] = None):
        self.bearer_token = bearer_token
        self.team_id = team_id
        self._deployments = {}

    async def _request(
        self, method: str, path: str, params: Optional[dict] = None
    ) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }

        params = {"teamId": self.team_id, **(params or {})}
        params = {key: value for key, value in params.items() if value is not None}

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            request = client.build_request(
                method, f"{API_BASE}{path}", headers=headers, params=params
            )
            print(f"REQUEST: {request.method} {request.url}")

            response = await client.send(request)
            print(f"RESPONSE: {response.status_code} {response.text}")

            return response

    async def deployments(
        self,
        *,
        state: Optional[str] = None,
        target: Optional[str] = None,
    ):
        response = await self._request(
            "GET",
            "/v6/deployments",
            {
                "state": state,
                "target": target,
                "limit": 100,
            },
        )

        self._deployments = {
            deployment["uid"]: deployment
            for deployment in response.json()["deployments"]
        }
        return self._deployments

    async def cancel_deployments(
        self,
        deployment_ids: list[str],
    ):
        responses = await asyncio.gather(
            *[
                self._request("PATCH", f"/v12/deployments/{deployment_id}/cancel")
                for deployment_id in deployment_ids
            ],
            return_exceptions=True,
        )

        for response in responses:
            # gather(return_exceptions=True) puts exceptions in here too
            if not isinstance(response, httpx.Response):
                print(f"REQUEST FAILED: {response!r}")

        return all(
            isinstance(r, httpx.Response) and r.status_code == 200 for r in responses
        )

    def open_deployment(self, deployment_id: str):
        deployment = self._deployments[deployment_id]
        webbrowser.open(deployment["inspectorUrl"])
