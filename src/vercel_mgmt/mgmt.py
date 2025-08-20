from textual.app import App, ComposeResult
from textual.widgets import Static


class VercelMGMT(App):
    def compose(self) -> ComposeResult:
        yield Static("Vercel MGMT")


def main():
    app = VercelMGMT()
    app.run()


if __name__ == "__main__":
    main()
