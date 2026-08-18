from textual import work, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, LoadingIndicator, DataTable
from rich.console import Console
from rich.text import Text
from vercel_mgmt.vercel import Vercel
from vercel_mgmt import watch as watch_mod
import argparse
import humanize
import os
import subprocess
import sys
from datetime import datetime


VI_MODE = os.environ.get("VI_MODE", "").lower() in ("1", "true", "yes", "on")


class VercelMGMT(App):
    TITLE = "Vercel MGMT"
    SUB_TITLE = "Non-production builds"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("space", "open", "Open"),
        ("w", "watch", "Watch"),
        ("c", "cancel", "Cancel Selected"),
        ("K" if VI_MODE else "k", "keep", "Keep Only Selected"),
    ] + ([
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "cursor_top", "Top", show=False),
        Binding("G", "cursor_bottom", "Bottom", show=False),
    ] if VI_MODE else [])

    def __init__(self, vercel: Vercel):
        super().__init__()
        self.vercel = vercel
        self.selected_deployments = set()

    def compose(self) -> ComposeResult:
        yield Header()
        yield LoadingIndicator()
        yield DataTable()
        yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        self.create_table()
        self.load_deployments()

    def create_table(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"

        table.add_column("", key="selected")
        table.add_column("created", key="created")
        table.add_column("state", key="state")
        table.add_column("project", key="project")
        table.add_column("creator", key="creator")
        table.add_column("branch", key="branch")
        table.add_column("commit", key="commit")

    def cursor_deployment_id(self):
        table = self.query_one(DataTable)
        if not len(table.rows):
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        return row_key.value

    def action_cancel(self) -> None:
        if not self.selected_deployments:
            return

        self.query_one(LoadingIndicator).display = True
        self.cancel_deployments()

    def action_keep(self) -> None:
        if not self.selected_deployments:
            return

        self.query_one(LoadingIndicator).display = True
        self.keep_only()

    def action_refresh(self) -> None:
        self.query_one(LoadingIndicator).display = True
        self.selected_deployments.clear()
        self.load_deployments()

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_cursor_up()

    def action_cursor_top(self) -> None:
        self.query_one(DataTable).move_cursor(row=0)

    def action_cursor_bottom(self) -> None:
        table = self.query_one(DataTable)
        table.move_cursor(row=len(table.rows) - 1)

    def action_open(self) -> None:
        deployment_id = self.cursor_deployment_id()
        if deployment_id is None:
            return
        self.vercel.open_deployment(deployment_id)

    def spawn_watcher(self, deployment_id: str) -> subprocess.Popen:
        env = os.environ.copy()
        env["VERCEL_TOKEN"] = self.vercel.bearer_token
        if self.vercel.team_id:
            env["VERCEL_TEAM_ID"] = self.vercel.team_id

        return subprocess.Popen(
            [sys.executable, "-m", "vercel_mgmt", "watch", deployment_id],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    def action_watch(self) -> None:
        deployment_id = self.cursor_deployment_id()
        if deployment_id is None:
            return

        self.spawn_watcher(deployment_id)

        deployment = self.vercel._deployments.get(deployment_id, {})
        label = Text(f"{deployment['name']}@{deployment['meta']['githubCommitRef']}", style="green")
        self.exit(label)

    @on(DataTable.RowSelected)
    def toggle_row_selection(self, event: DataTable.RowSelected) -> None:
        table = event.control
        row_key = event.row_key
        deployment_id = row_key.value
        if deployment_id in self.selected_deployments:
            self.selected_deployments.remove(deployment_id)
            table.update_cell(row_key, "selected", " ")
        else:
            self.selected_deployments.add(deployment_id)
            table.update_cell(row_key, "selected", "✔")

        row_idx, _ = table.cursor_coordinate
        if row_idx < len(table.rows) - 1:
            table.move_cursor(row=row_idx + 1)

    @work(exclusive=True)
    async def load_deployments(self) -> None:
        deployments = await self.vercel.deployments(
            state="QUEUED,BUILDING", target="preview"
        )
        self.query_one(LoadingIndicator).display = False
        table = self.query_one(DataTable)
        table.clear()
        for deployment_id, deployment in deployments.items():
            createdAt = datetime.fromtimestamp(int(deployment["created"]) / 1000)
            buildingAt = datetime.fromtimestamp(int(deployment["buildingAt"]) / 1000) if deployment.get('buildingAt') else None

            table.add_row(
                Text(" "),
                Text(
                    humanize.naturaltime(createdAt),
                    style="cyan",
                ),
                Text(
                    deployment["state"] + (f" ({int((datetime.now() - buildingAt).total_seconds() / 60)}m)" if deployment["state"] == "BUILDING" else ''),
                    style="yellow" if deployment["state"] == "BUILDING" else None,
                ),
                Text(deployment["name"]),
                Text(deployment["creator"]["username"], style="italic green"),
                Text(deployment["meta"]["githubCommitRef"], style="lightblue"),
                Text(
                    deployment["meta"]["githubCommitMessage"][:50]
                    + (
                        "..."
                        if len(deployment["meta"]["githubCommitMessage"]) > 50
                        else ""
                    ),
                ),
                key=deployment_id,
            )

    @work(exclusive=True)
    async def cancel_deployments(self) -> None:
        deployment_ids = list(self.selected_deployments)
        await self.vercel.cancel_deployments(deployment_ids)
        self.selected_deployments.clear()
        self.load_deployments()

    @work(exclusive=True)
    async def keep_only(self) -> None:
        rows_keys= self.query_one(DataTable).rows.keys()
        all_deployment_ids = [row_key.value for row_key in rows_keys]
        deployment_ids = list(set(all_deployment_ids) - self.selected_deployments)
        await self.vercel.cancel_deployments(deployment_ids)
        self.selected_deployments.clear()
        self.load_deployments()

def main():
    parser = argparse.ArgumentParser(description="Vercel Management Tool")

    parser.add_argument(
        "--token",
        "-t",
        default=os.environ.get("VERCEL_TOKEN"),
        help="Vercel bearer token (or $VERCEL_TOKEN)",
    )
    parser.add_argument(
        "--team-id",
        "-tid",
        default=os.environ.get("VERCEL_TEAM_ID"),
        help="Vercel team ID (or $VERCEL_TEAM_ID, optional)",
    )

    subparsers = parser.add_subparsers(dest="command")
    watch_parser = subparsers.add_parser(
        "watch", help="Wait for a deployment to finish, then open it"
    )
    watch_parser.add_argument("deployment_id")
    watch_parser.add_argument("--interval", type=int, default=15, help="Poll seconds")

    args = parser.parse_args()

    vercel = Vercel(args.token, args.team_id)

    if args.command == "watch":
        raise SystemExit(
            watch_mod.run(vercel, args.deployment_id, interval=args.interval)
        )

    mgmt = VercelMGMT(vercel)

    watching = mgmt.run()
    if watching:
        message = Text("Will open ")
        message.append_text(watching)
        message.append(" in your browser once the build finishes")
        Console().print(message)


if __name__ == "__main__":
    main()
