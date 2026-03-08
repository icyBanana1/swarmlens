from __future__ import annotations

import http.server
import socketserver
import webbrowser
from pathlib import Path


def serve_report(report_dir: str | Path, port: int = 8765, open_browser: bool = True) -> None:
    report_dir = Path(report_dir).resolve()
    if not (report_dir / "report.html").exists():
        raise FileNotFoundError(f"report.html not found in {report_dir}")

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(report_dir), **kwargs)

    with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
        url = f"http://127.0.0.1:{port}/report.html"
        if open_browser:
            webbrowser.open(url)
        print(f"[+] SwarmLens dashboard running at {url}")
        print("[+] Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[+] Dashboard stopped")
