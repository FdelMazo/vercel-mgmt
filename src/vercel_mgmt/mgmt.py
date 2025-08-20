from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, LoadingIndicator, DataTable
from vercel_mgmt.vercel import Vercel
import argparse


class VercelMGMT(App):
    TITLE = "Vercel MGMT"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, vercel: Vercel):
        super().__init__()
        self.vercel = vercel

    def compose(self) -> ComposeResult:
        yield Header()
        yield LoadingIndicator()
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        self.load_deployments()

    @work(exclusive=True)
    async def load_deployments(self) -> None:
        deployments = await self.vercel.deployments(state="BUILDING")
        self.query_one(LoadingIndicator).remove()
        table = self.query_one(DataTable)
        table.add_columns("Name")
        for deployment in deployments:
            table.add_row(
                deployment["name"],
            )


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
