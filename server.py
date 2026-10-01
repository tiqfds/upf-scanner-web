"""Local page for one ingredient-list photo.

The NOVA group comes from the scanner package in the original project.
This server does not keep a second copy of those rules.
"""

from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from card import announcement, card_from_scan

PORT = 3000
MAX_BYTES = 20_000_000
_SCAN = threading.Lock()
_accept_photo = None
_client_error_body = None

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ultra-processed food</title>
  <style>
    body { margin: 0; background: #F6F8F7; color: #1B2A2F;
      font-family: system-ui, sans-serif; font-size: 15px; }
    main { max-width: 28rem; margin: 0 auto; padding: 32px 16px;
      display: flex; flex-direction: column; gap: 16px; }
    h1 { font-size: 22px; line-height: 28px; margin: 0; }
    p { margin: 0; }
    .muted { color: #5B6B70; }
    button, .choose { min-height: 44px; border-radius: 12px; border: 0;
      background: #2C4BD1; color: white; font-size: 15px; font-weight: 500; }
    .choose { display: flex; align-items: center; justify-content: center;
      border: 1px solid #DCE3E1; background: white; color: #1B2A2F; cursor: pointer; }
    button { cursor: pointer; }
    button:disabled { opacity: 0.5; }
    input { position: absolute; width: 1px; height: 1px; overflow: hidden;
      clip: rect(0 0 0 0); }
    img { width: 100%; max-height: 14rem; object-fit: contain; background: white;
      border-radius: 12px; }
    article { background: white; border-radius: 16px; padding: 20px;
      display: flex; flex-direction: column; gap: 16px; }
    ul { list-style: none; margin: 0; padding: 0; display: flex;
      flex-direction: column; gap: 8px; }
    li.nested { padding-left: 16px; color: #5B6B70; }
    strong { font-weight: 600; }
  </style>
</head>
<body>
  <main id="app"></main>
  <script>
    const colors = {1: "#3F8F5B", 2: "#6F8F3A", 3: "#B7801A", 4: "#7A3E6E"};
    const app = document.getElementById("app");
    let file = null;
    let preview = "";

    function escapeText(value) {
      return String(value).replace(/[&<>]/g, (ch) => (
        {"&": "&amp;", "<": "&lt;", ">": "&gt;"}[ch]
      ));
    }

    function ingredientHtml(item, nested) {
      const category = item.marker && item.category ? " │ " + item.category : "";
      const name = item.marker ? "<strong>" + escapeText(item.name) + "</strong>" : escapeText(item.name);
      const children = (item.children || []).map((child) => ingredientHtml(child, true)).join("");
      return "<li class=\\"" + (nested && !item.marker ? "nested" : "") + "\\"><p>• " + name + escapeText(category) + "</p>" + (children ? "<ul>" + children + "</ul>" : "") + "</li>";
    }

    function showForm(message, isError) {
      const note = message ? "<p class=\\"muted\\" role=\\"" + (isError ? "alert" : "status") + "\\">" + escapeText(message) + "</p>" : "";
      const picture = preview ? "<img src=\\"" + preview + "\\" alt=\\"Selected food photo\\">" : "";
      const chosen = file ? "<p class=\\"muted\\">" + escapeText(file.name) + "</p>" : "";
      app.innerHTML = "<form><h1>Check a food label</h1><p class=\\"muted\\">Choose a photo that shows the ingredient list.</p><label class=\\"choose\\">Choose a photo<input type=\\"file\\" accept=\\"image/*\\"></label>" + chosen + picture + "<button type=\\"submit\\"" + (file ? "" : " disabled") + ">Check this photo</button>" + note + "</form>";
      app.querySelector("input").addEventListener("change", (event) => {
        file = event.target.files && event.target.files[0] ? event.target.files[0] : null;
        if (preview) URL.revokeObjectURL(preview);
        preview = file ? URL.createObjectURL(file) : "";
        showForm("", false);
      });
      app.querySelector("form").addEventListener("submit", submitPhoto);
    }

    function showCard(card) {
      const color = colors[card.group] || "#1B2A2F";
      const notice = card.notice && card.title ? "<p class=\\"muted\\">" + escapeText(card.notice) + "</p>" : "";
      const items = (card.ingredients || []).map((item) => ingredientHtml(item, false)).join("");
      const list = items ? "<ul>" + items + "</ul>" : "";
      const picture = preview ? "<img src=\\"" + preview + "\\" alt=\\"Submitted food photo\\">" : "";
      app.innerHTML = "<article aria-label=\\"" + escapeText(card.announcement || card.title) + "\\">" + picture + "<h1 style=\\"color:" + color + "\\">" + escapeText(card.title) + "</h1>" + notice + list + "<button type=\\"button\\">Okay</button></article>";
      app.querySelector("button").addEventListener("click", () => {
        file = null;
        if (preview) URL.revokeObjectURL(preview);
        preview = "";
        showForm("", false);
      });
    }

    async function submitPhoto(event) {
      event.preventDefault();
      if (!file) {
        showForm("Choose a photo of the ingredient list.", true);
        return;
      }
      showForm("Reading the ingredient list.", false);
      app.querySelector("button").disabled = true;
      try {
        const response = await fetch("/scan", {
          method: "POST",
          headers: {"Content-Type": file.type || "image/jpeg"},
          body: file,
        });
        const payload = await response.json();
        if (!response.ok) {
          showForm(payload.error || "The scan did not finish. Try another photo.", true);
          return;
        }
        showCard(payload);
      } catch (error) {
        showForm("The scan did not finish. Try another photo.", true);
      }
    }

    showForm("", false);
  </script>
</body>
</html>
"""


def scanner_root() -> Path:
    """The original project, where the scanner package lives."""
    chosen = os.environ.get("UPF_SCANNER_ROOT")
    if chosen:
        return Path(chosen)
    return Path(__file__).resolve().parent.parent / "Ultra-processed-food"


def load_scanner():
    root = scanner_root()
    if not (root / "scanner" / "live.py").is_file():
        raise SystemExit(
            "The scanner package was not found.\n"
            "Set UPF_SCANNER_ROOT to the original project folder."
        )
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    from scanner.live import client_error_body, preview_photo
    from scanner.release_session import ReleaseUnavailable, load_release

    # The scanner's own server loads the named release before it takes a
    # photo. Without it every scan stops with ReleaseUnavailable.
    try:
        print(f"kb_version={load_release()}", flush=True)
    except ReleaseUnavailable as error:
        raise SystemExit(
            f"{error}\nStart the review database (upf-dev-pg) and check "
            "OWNER_REVIEWER_PASSWORD in the original project's .env."
        ) from None

    return preview_photo, client_error_body


def _boundary(content_type: str) -> bytes | None:
    if "boundary=" not in content_type:
        return None
    raw = content_type.split("boundary=", 1)[1].strip()
    if raw.startswith('"'):
        raw = raw[1:].split('"', 1)[0]
    else:
        raw = raw.split(";", 1)[0].strip()
    if not raw:
        return None
    return raw.encode("utf-8")


def photo_from_multipart(body: bytes, content_type: str) -> bytes | None:
    boundary = _boundary(content_type)
    if boundary is None:
        return None
    for part in body.split(b"--" + boundary):
        if b"Content-Disposition" not in part:
            continue
        header, _, data = part.partition(b"\r\n\r\n")
        if b'name="photo"' not in header and b"name=photo" not in header:
            continue
        data = data.rstrip(b"\r\n")
        if data.endswith(b"--"):
            data = data[:-2].rstrip(b"\r\n")
        return data or None
    return None


def photo_bytes(content_type: str, body: bytes) -> bytes | None:
    kind = content_type.split(";", 1)[0].strip().lower()
    if kind.startswith("image/") or kind in ("", "application/octet-stream"):
        return body or None
    if "multipart/form-data" in content_type:
        return photo_from_multipart(body, content_type)
    return None


def _note(text: str) -> None:
    print(text, flush=True)


def scan_image(image: bytes) -> tuple[int, dict[str, Any]]:
    """Run one photo through the original scanner and return the card."""
    _note(f"scan start  {len(image)} bytes")
    try:
        with _SCAN:
            result = _accept_photo(image)
    except BaseException as error:
        _note(f"scan failed  {type(error).__name__}")
        if _client_error_body is None:
            return 500, {"error": "The scan did not finish. Try another photo."}
        try:
            return 500, _client_error_body(error)
        except BaseException:
            return 500, {"error": "The scan did not finish. Try another photo."}
    if result.get("error"):
        return 500, {"error": "The scan did not finish. Try another photo."}
    card = card_from_scan(result)
    card["announcement"] = announcement(card)
    _note(f"scan done  {card.get('title')}")
    return 200, card


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path not in ("/", "/index.html"):
            self._json(404, {"error": "Not found"})
            return
        encoded = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        if urlparse(self.path).path not in ("/scan", "/api/scan"):
            self._json(404, {"error": "Not found"})
            return
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            self._json(400, {"error": "Choose a photo."})
            return
        if length > MAX_BYTES:
            self._json(400, {"error": "That file is too large. Choose a smaller photo."})
            return
        body = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")
        _note(f"photo received  {length} bytes")
        image = photo_bytes(content_type, body)
        if not image:
            self._json(400, {"error": "Choose a photo."})
            return
        try:
            code, payload = scan_image(image)
        except BaseException:
            _note("scan failed  uncaught")
            code, payload = 500, {"error": "The scan did not finish. Try another photo."}
        self._json(code, payload)

    def log_message(self, fmt, *args):
        return

    def _json(self, code, payload):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def connect_scanner() -> None:
    """Load the original scanner once. Both front ends call this."""
    global _accept_photo, _client_error_body
    _accept_photo, _client_error_body = load_scanner()


def serve(port: int = PORT) -> None:
    connect_scanner()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Open http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
