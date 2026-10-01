"""Knowledge importers: uploaded files and web URLs.

Security:
* uploads are size-limited and restricted to .txt / .md / .pdf
* URL import only allows http(s), resolves the host and refuses private,
  loopback, link-local and reserved addresses (SSRF protection), re-checks
  every redirect hop, and caps the downloaded size
"""

from __future__ import annotations

import io
import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import get_settings

ALLOWED_EXTENSIONS = {".txt", ".md", ".markdown", ".pdf"}
MAX_REDIRECTS = 3


class ImportError_(ValueError):
    """User-facing import failure (bad file, blocked URL, unreadable page…)."""


# ---------------------------------------------------------------- files


def extract_file_text(filename: str, data: bytes) -> str:
    settings = get_settings()
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise ImportError_(f"File is too large (max {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB)")
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ImportError_("Unsupported file type. Upload a .txt, .md or .pdf file")
    if ext == ".pdf":
        if not data.startswith(b"%PDF"):
            raise ImportError_("That file does not look like a valid PDF")
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            text = "\n\n".join((page.extract_text() or "") for page in reader.pages[:200])
        except Exception as exc:  # pypdf raises many exception types for malformed files
            raise ImportError_("Could not read text from that PDF") from exc
    else:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
    text = text.replace("\x00", "").strip()
    if not text:
        raise ImportError_("No readable text was found in that file")
    return text[: settings.MAX_KNOWLEDGE_CHARS]


# ---------------------------------------------------------------- URLs


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "iframe"}
    BLOCK = {"p", "div", "section", "article", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br", "tr", "blockquote", "pre"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.title = ""
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP:
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif not self._skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        raw = "".join(self.parts)
        lines = [re.sub(r"[ \t\xa0]+", " ", line).strip() for line in raw.split("\n")]
        paragraphs: list[str] = []
        for line in lines:
            if line:
                paragraphs.append(line)
            elif paragraphs and paragraphs[-1] != "":
                paragraphs.append("")
        return re.sub(r"\n{3,}", "\n\n", "\n".join(paragraphs)).strip()


def _assert_public_host(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ImportError_("Only http and https URLs can be imported")
    host = parsed.hostname
    if not host:
        raise ImportError_("That URL has no host")
    if parsed.username or parsed.password:
        raise ImportError_("URLs with embedded credentials are not allowed")
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise ImportError_("Could not resolve that host") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            not ip.is_global  # also covers CGNAT 100.64.0.0/10 and other special-purpose ranges
            or ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ImportError_("That address points to a private or internal network and cannot be imported")


def fetch_url_text(url: str) -> tuple[str, str]:
    """Return ``(title, text)`` for a public web page or plain-text URL."""
    settings = get_settings()
    current = url.strip()
    with httpx.Client(timeout=settings.URL_FETCH_TIMEOUT_SECONDS, follow_redirects=False) as client:
        for _ in range(MAX_REDIRECTS + 1):
            _assert_public_host(current)
            try:
                with client.stream(
                    "GET", current, headers={"User-Agent": "PersonaTwin/1.0 (knowledge import)"}
                ) as resp:
                    if resp.is_redirect:
                        location = resp.headers.get("location")
                        if not location:
                            raise ImportError_("The page redirected without a location")
                        current = urljoin(current, location)
                        continue
                    if resp.status_code >= 400:
                        raise ImportError_(f"The page returned HTTP {resp.status_code}")
                    content_type = resp.headers.get("content-type", "").lower()
                    if not any(t in content_type for t in ("text/html", "text/plain", "text/markdown", "application/xhtml")):
                        raise ImportError_("Only HTML and plain-text pages can be imported")
                    body = bytearray()
                    for chunk in resp.iter_bytes():
                        body.extend(chunk)
                        if len(body) > settings.MAX_UPLOAD_BYTES:
                            raise ImportError_("That page is too large to import")
                    charset = resp.encoding or "utf-8"
            except httpx.HTTPError as exc:
                raise ImportError_("Could not download that page") from exc
            decoded = bytes(body).decode(charset, errors="replace")
            if "html" in content_type:
                parser = _TextExtractor()
                parser.feed(decoded)
                title, text = parser.title.strip(), parser.text()
            else:
                title, text = "", decoded.strip()
            if len(text) < 40:
                raise ImportError_("Not enough readable text was found on that page")
            return title[:200], text[: settings.MAX_KNOWLEDGE_CHARS]
    raise ImportError_("Too many redirects")
