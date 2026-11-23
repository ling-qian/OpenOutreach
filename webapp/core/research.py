"""Evidence-first website research with bounded fetching and conservative heuristics."""
from __future__ import annotations

import ipaddress
import socket
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

MAX_BYTES = 1_500_000
TIMEOUT = 12
USER_AGENT = "AcquisitionResearchBot/0.1 (+website audit; contact: operator)"


def _public_http_url(raw: str) -> str:
    parsed = urllib.parse.urlsplit((raw or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a valid http(s) website URL.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not accepted.")
    host = parsed.hostname.encode("idna").decode("ascii")
    try:
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except OSError as exc:
        raise ValueError("The website host could not be resolved.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("Private, local, and non-public network addresses are not allowed.")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "Redirects are not followed; submit the canonical URL.", headers, fp)


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = False
        self.in_title = False
        self.title_parts = []
        self.text_parts = []
        self.headings = []
        self.links = []
        self.active_link = None
        self.images = 0
        self.forms = 0
        self.meta = {}
        self.canonical = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag in {"h1", "h2", "h3"}:
            self.headings.append({"tag": tag, "text": ""})
            self.title = True
        elif tag == "meta":
            key = (attrs.get("name") or attrs.get("property") or "").lower()
            if key in {"description", "og:title", "og:description", "robots"}:
                self.meta[key] = attrs.get("content", "")[:1000]
        elif tag == "link" and "canonical" in (attrs.get("rel") or "").lower():
            self.canonical = attrs.get("href", "")[:1000]
        elif tag == "a":
            self.links.append({"text": "", "href": attrs.get("href", "")[:1000]})
            self.active_link = len(self.links) - 1
        elif tag == "img":
            self.images += 1
        elif tag == "form":
            self.forms += 1

    def handle_endtag(self, tag):
        if tag == "a":
            self.active_link = None
        if tag == "title":
            self.in_title = False
        if tag in {"h1", "h2", "h3"}:
            self.title = False

    def handle_data(self, data):
        value = " ".join(data.split())
        if not value:
            return
        if self.in_title:
            self.title_parts.append(value)
        self.text_parts.append(value)
        if self.title and self.headings:
            self.headings[-1]["text"] = (self.headings[-1]["text"] + " " + value).strip()[:300]
        if getattr(self, "active_link", None) is not None:
            link = self.links[self.active_link]
            if len(link["text"]) < 180:
                link["text"] = (link["text"] + " " + value).strip()[:180]


def fetch_page(url: str) -> dict:
    safe_url = _public_http_url(url)
    opener = urllib.request.build_opener(_NoRedirect())
    request = urllib.request.Request(safe_url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with opener.open(request, timeout=TIMEOUT) as response:
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"Website returned {content_type}, not HTML.")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Website HTML exceeded the 1.5 MB research limit.")
        charset = response.headers.get_content_charset() or "utf-8"
        html = raw.decode(charset, errors="replace")
        final_url = response.geturl()
    parser = _PageParser()
    parser.feed(html)
    return {
        "url": final_url, "status": response.status, "title": " ".join(parser.title_parts)[:300],
        "meta": parser.meta, "headings": parser.headings[:40], "links": parser.links[:250],
        "images": parser.images, "forms": parser.forms,
        "text": " ".join(parser.text_parts)[:12000],
    }


def analyze_page(page: dict) -> list[dict]:
    findings = []
    meta = page["meta"]
    h1 = [h for h in page["headings"] if h["tag"] == "h1" and h["text"]]
    if not page["title"]:
        findings.append(("seo", "Missing page title", "The homepage HTML has no usable title element.", 95))
    if not meta.get("description"):
        findings.append(("seo", "Missing meta description", "No meta description was found in the homepage HTML.", 90))
    if not h1:
        findings.append(("seo", "Missing H1 heading", "No non-empty H1 heading was found.", 85))
    elif len(h1) > 1:
        findings.append(("seo", "Multiple H1 headings", f"Found {len(h1)} H1 headings; review whether the page has one clear primary topic.", 65))
    if "noindex" in page["meta"].get("robots", "").lower():
        findings.append(("seo", "Homepage may be noindexed", "The robots meta directive contains noindex.", 95))
    text = page["text"].lower()
    local_terms = ("address", "phone", "contact", "location", "hours", "service area")
    if not any(term in text for term in local_terms):
        findings.append(("local_seo", "No obvious local business details", "The extracted homepage text did not contain common address, phone, location, hours, or service-area terms. This is a signal to review, not proof that the details are absent site-wide.", 55))
    cta_terms = ("get a quote", "book", "schedule", "contact us", "free consultation", "request a quote", "get started")
    cta_links = [link for link in page["links"] if any(term in (link["text"] + " " + link["href"]).lower() for term in cta_terms)]
    if not cta_links and page["forms"] == 0:
        findings.append(("conversion", "No obvious primary conversion action", "The homepage contains no detected contact/booking/quote CTA link and no HTML form. Check other pages and rendered interactions before concluding the site lacks a conversion path.", 60))
    return [{"category": c, "title": t, "detail": d, "confidence": score} for c, t, d, score in findings]
