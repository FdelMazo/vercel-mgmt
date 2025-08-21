from textual import work, on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, LoadingIndicator, DataTable
from vercel_mgmt.vercel import Vercel
import argparse
import humanize
from datetime import datetime


class VercelMGMT(App):
    TITLE = "Vercel MGMT"
    SUB_TITLE = "Non-production builds"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, vercel: Vercel):
        super().__init__()
        self.vercel = vercel
        self.selected_deployments = set()

    def compose(self) -> ComposeResult:
        yield Header()
        yield LoadingIndicator()
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        self.load_deployments()

    @work(exclusive=True)
    async def load_deployments(self) -> None:
        deployments = await self.vercel.deployments(
            state="QUEUED,BUILDING,READY", target="preview"
        )
        self.query_one(LoadingIndicator).remove()
        self.populate_table(deployments)

    def populate_table(self, deployments: list[dict]) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"

        table.add_column("", key="selected")
        table.add_column("created", key="created")
        table.add_column("state", key="state")
        table.add_column("project", key="project")
        table.add_column("creator", key="creator")
        table.add_column("branch", key="branch")
        table.add_column("commit", key="commit")
        for deployment in deployments:
            table.add_row(
                " ",
                humanize.naturaltime(
                    datetime.fromtimestamp(int(deployment["created"]) / 1000)
                ),
                deployment["state"],
                deployment["name"],
                deployment["creator"]["username"],
                deployment["meta"]["githubCommitRef"],
                deployment["meta"]["githubCommitMessage"][:50]
                + (
                    "..." if len(deployment["meta"]["githubCommitMessage"]) > 50 else ""
                ),
                key=deployment["uid"],
            )

    @on(DataTable.RowSelected)
    def toggle_row_selection(self, event: DataTable.RowSelected) -> None:
        table = event.control
        row_key = event.row_key
        if row_key in self.selected_deployments:
            self.selected_deployments.remove(row_key)
            table.update_cell(row_key, "selected", " ")
        else:
            self.selected_deployments.add(row_key)
            table.update_cell(row_key, "selected", "✔")


def main():
    parser = argparse.ArgumentParser(description="Vercel Management Tool")
    parser.add_argument("--token", "-t", required=True, help="Vercel bearer token")
    parser.add_argument("--team-id", "-tid", help="Vercel team ID (optional)")
    args = parser.parse_args()

    vercel = Vercel(args.token, args.team_id)
    mgmt = VercelMGMT(vercel)
    mgmt.run()


if __name__ == "__main__":
    main()
