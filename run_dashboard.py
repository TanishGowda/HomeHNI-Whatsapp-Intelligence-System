import webbrowser
from threading import Timer

from dashboard_app import create_app


def open_browser(url: str) -> None:
    try:
        webbrowser.open(url)
    except Exception:
        # Failing to open the browser should not stop the server
        pass


def main() -> None:
    app = create_app()
    port = 5000
    url = f"http://127.0.0.1:{port}/"

    # Open browser shortly after server starts
    Timer(1.0, open_browser, args=(url,)).start()

    # Run Flask development server (sufficient for local use by your client)
    app.run(host="127.0.0.1", port=port, debug=True)


if __name__ == "__main__":
    main()


