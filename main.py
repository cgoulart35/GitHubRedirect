"""GitHubRedirect — a tiny HTTP(S) redirect server.

Serves every redirect listed in the REDIRECTS environment variable, one listener
per port. Each line is "<name> <port> <url>"; blank lines and # comments are
ignored:

    REDIRECTS="
      docs     5010  https://example.github.io/docs/
      discord  5011  https://discord.gg/example
    "

GET / on a redirect's port answers 302 to its URL. HTTPS is used when CERT_FILE
and KEY_FILE point at existing files; otherwise it serves plain HTTP.
Logs go to stdout, one line per request, tagged with the redirect's name.
"""
import logging
import os
import signal
import sys
import threading

from flask import Flask, redirect, request
from werkzeug.serving import make_server

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(levelname)s %(asctime)s [%(name)s] %(message)s",
)
logging.getLogger("werkzeug").setLevel(logging.WARNING)  # we log each request ourselves
log = logging.getLogger("github-redirect")


def parse_redirects(text):
    """Parse REDIRECTS into a list of (name, port, url)."""
    routes = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 3 or not parts[1].isdigit():
            raise ValueError(f"REDIRECTS line {lineno}: expected '<name> <port> <url>', got {raw!r}")
        routes.append((parts[0], int(parts[1]), parts[2]))
    ports = [port for _, port, _ in routes]
    if len(ports) != len(set(ports)):
        raise ValueError("REDIRECTS: each redirect needs its own port")
    return routes


def make_app(name, url):
    app = Flask(name)
    route_log = logging.getLogger(name)

    @app.route("/")
    def go():
        route_log.info("%s -> %s", request.remote_addr, url)
        return redirect(url)

    return app


def ssl_context():
    cert, key = os.environ.get("CERT_FILE", ""), os.environ.get("KEY_FILE", "")
    if cert and key and os.path.isfile(cert) and os.path.isfile(key):
        return (cert, key)
    return None


def main():
    try:
        routes = parse_redirects(os.environ.get("REDIRECTS", ""))
    except ValueError as err:
        log.error("%s", err)
        return 1
    if not routes:
        log.error("REDIRECTS is empty — nothing to serve")
        return 1

    ctx = ssl_context()
    scheme = "https" if ctx else "http"
    servers = []
    for name, port, url in routes:
        server = make_server("0.0.0.0", port, make_app(name, url), threaded=True, ssl_context=ctx)
        threading.Thread(target=server.serve_forever, name=name, daemon=True).start()
        servers.append(server)
        log.info("%s: %s://0.0.0.0:%d/ -> %s", name, scheme, port, url)

    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    stop.wait()
    for server in servers:
        server.shutdown()
    log.info("stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
