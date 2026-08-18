import asyncio
import signal
import webbrowser
from vercel_mgmt.vercel import Vercel


TERMINAL_STATES = {"READY": 0, "ERROR": 1, "CANCELED": 2}
TIMED_OUT = 3
TIMEOUT_MIN = 45


async def watch(
    vercel: Vercel,
    deployment_id: str,
    *,
    interval: int = 15,
) -> int:
    # Kill after N minutes
    signal.alarm(TIMEOUT_MIN * 60)

    while True:
        try:
            deployment = await vercel.deployment(deployment_id)
        except Exception as e:
            # Treat a failed poll as "no news"; the alarm above is what stops us.
            print(f"ERROR: {e!r}")
            deployment = {}

        state = deployment.get("readyState")
        if state in TERMINAL_STATES:
            print(f"{deployment_id} {state}")
            webbrowser.open(deployment["inspectorUrl"])
            return TERMINAL_STATES[state]

        await asyncio.sleep(interval)


def run(vercel: Vercel, deployment_id: str, *, interval: int) -> int:
    try:
        return asyncio.run(watch(vercel, deployment_id, interval=interval))
    except KeyboardInterrupt:
        return TIMED_OUT
