from __future__ import annotations

import sys
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from serve_viewer import is_app_safe_viewer_url, serve_viewer  # noqa: E402


class AppSafeViewerUrlTests(unittest.TestCase):
    """Locks the rule that prevents the wry-0.55.1 InvalidUri(InvalidFormat) panic.

    The Copilot App Browser canvas (wry/WebView2) panics when the opened page URL
    is not a valid ``http::Uri`` and its IPC bridge posts a message. Only
    non-empty-authority http(s) URLs are safe; ``file:///`` forms are not.
    """

    def test_loopback_http_is_safe(self) -> None:
        self.assertTrue(is_app_safe_viewer_url("http://127.0.0.1:49215/viewer.html"))
        self.assertTrue(is_app_safe_viewer_url("http://localhost:8080/gen/viewer.html"))

    def test_file_scheme_is_unsafe(self) -> None:
        # The exact family of URL that crashed github-app@1.0.25 on Windows.
        self.assertFalse(is_app_safe_viewer_url("file:///C:/repos/proj/gen/viewer.html"))
        self.assertFalse(is_app_safe_viewer_url("file:///home/user/gen/viewer.html"))
        self.assertFalse(is_app_safe_viewer_url("file:///viewer.html"))

    def test_other_schemes_unsafe(self) -> None:
        for url in ("about:blank", "data:text/html,<h1>x</h1>", "blob:null/1", ""):
            self.assertFalse(is_app_safe_viewer_url(url), url)


class ServeViewerLoopbackTests(unittest.TestCase):
    def test_serves_viewer_over_safe_loopback_url(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "viewer.html").write_text("<html><body>Overview</body></html>", encoding="utf-8")
            server, base_url = serve_viewer(tmp)
            try:
                # The URL handed to the App canvas must be panic-safe by construction.
                self.assertTrue(is_app_safe_viewer_url(base_url + "viewer.html"))
                self.assertTrue(base_url.startswith("http://127.0.0.1:"))
                with urllib.request.urlopen(base_url + "viewer.html", timeout=5) as resp:
                    body = resp.read().decode("utf-8")
                self.assertEqual(resp.status, 200)
                self.assertIn("Overview", body)
            finally:
                server.shutdown()
                server.server_close()

    def test_missing_directory_raises(self) -> None:
        with self.assertRaises(NotADirectoryError):
            serve_viewer(Path(__file__).resolve().parent / "does-not-exist-xyz")


if __name__ == "__main__":
    unittest.main()
