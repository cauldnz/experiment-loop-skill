"""Serve a generated Viewer over loopback HTTP instead of ``file://``.

Why this exists
---------------
The GitHub Copilot desktop app hosts its Browser canvas with ``wry`` (WebView2 on
Windows). When a page is opened via ``file:///C:/...`` and the host's IPC bridge
posts a web message, ``wry`` builds ``http::Request::builder().uri(<page-url>)
.body(..).unwrap()`` (wry-0.55.1 ``src/webview2/mod.rs:910``). The ``http`` crate's
``Uri`` parser rejects a ``file://`` URL that has an *empty authority*
(``file:///...``) with ``InvalidUri(InvalidFormat)``, so the ``.unwrap()`` panics
and tears down the whole app.

A ``http://127.0.0.1:<port>/`` URL has a non-empty authority and parses cleanly,
so serving the Viewer over loopback avoids the panic entirely. The Viewer is fully
self-contained (no sub-resource requests), so loopback serving renders it
identically to a direct disk open.

This helper is pure standard library and has no network egress; it binds only to
the loopback interface.
"""

from __future__ import annotations

import argparse
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

LOOPBACK_HOST = "127.0.0.1"


def is_app_safe_viewer_url(url: str) -> bool:
    """Return True if ``url`` is safe to open in the Copilot App Browser canvas.

    The wry/WebView2 host panics on any page URL that is not a valid ``http::Uri``
    once its IPC bridge posts a message. A URL is safe only when it carries a
    non-empty authority under an ``http``/``https`` scheme. ``file://`` URLs with an
    empty authority (the ``file:///path`` form produced by opening from disk) are
    unsafe and must never be handed to the App canvas.
    """
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return False
    return bool(parts.hostname)


def serve_viewer(
    directory: Path | str,
    port: int = 0,
    host: str = LOOPBACK_HOST,
) -> tuple[ThreadingHTTPServer, str]:
    """Start a background loopback HTTP server rooted at ``directory``.

    Returns ``(server, base_url)``. ``port=0`` binds an ephemeral port. The server
    runs on a daemon thread; call ``server.shutdown()`` to stop it. The returned
    ``base_url`` is guaranteed to satisfy :func:`is_app_safe_viewer_url`.
    """
    directory = Path(directory).resolve()
    if not directory.is_dir():
        raise NotADirectoryError(directory)
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer((host, port), handler)
    bound_host, bound_port = server.server_address[0], server.server_address[1]
    base_url = f"http://{bound_host}:{bound_port}/"
    thread = threading.Thread(target=server.serve_forever, name="viewer-loopback", daemon=True)
    thread.start()
    return server, base_url


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", required=True, help="Directory containing viewer.html")
    parser.add_argument("--port", type=int, default=0, help="Port (0 = ephemeral)")
    parser.add_argument("--file", default="viewer.html", help="Viewer file to link")
    args = parser.parse_args(argv)

    server, base_url = serve_viewer(args.dir, port=args.port)
    viewer_url = base_url + args.file
    print(f"Serving {args.dir} at {base_url}")
    print(f"Open the Viewer at: {viewer_url}")
    print("Do NOT open the Viewer via file:// in the Copilot App Browser canvas.")
    print("Press Ctrl+C to stop.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
