#!/usr/bin/env python3
"""Validate a clean Hugo output without network or third-party dependencies."""
import argparse
import base64
import fnmatch
import gzip
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.feed(source)

    def handle_starttag(self, tag, attributes):
        self.elements.append((tag, dict(attributes)))


def require(condition, message):
    if not condition:
        raise SystemExit("FAIL: " + message)


def check(build):
    require((build / "index.html").is_file(), "build output is missing index.html")
    forbidden = {"docs", "scripts", "font-study", "name-preview", "vertical-margin", "vertical-replace", "bilingual", ".git"}
    for path in build.rglob("*"):
        relative = path.relative_to(build)
        require(not (set(relative.parts) & forbidden), f"non-production path: {relative}")
        if path.is_file():
            require(path.suffix not in {".py", ".toml", ".md", ".json", ".ttf"} or "vendor" in relative.parts,
                    f"unexpected source/font file: {relative}")

    assets = list((build / "assets").glob("*"))
    require(assets, "fingerprinted assets missing")
    for asset in assets:
        match = re.search(r"\.([a-f0-9]{64})\.[^.]+$", asset.name)
        require(match is not None and asset.is_file(), f"mutable asset under immutable namespace: {asset.name}")
        require(hashlib.sha256(asset.read_bytes()).hexdigest() == match.group(1), f"wrong fingerprint: {asset.name}")

    styles = [p for p in assets if p.suffix == ".css"]
    scripts = [p for p in assets if p.suffix == ".js"]
    name_fonts = [p for p in assets if p.name.startswith("zhuque-name.")]
    require(len(styles) == len(scripts) == len(name_fonts) == 1, "expected one CSS, JS, and Chinese font asset")
    name_font = name_fonts[0]
    require(name_font.read_bytes().startswith(b"wOF2"), "Chinese font is not WOFF2")
    require(name_font.stat().st_size <= 4096, "Chinese name font exceeds 4 KiB budget")
    css = styles[0].read_text()
    require("/assets/" + name_font.name in css, "CSS does not use the fingerprinted font")
    require((build / "fonts/ZhuqueFangsong-OFL.txt").is_file(), "Chinese font license missing")
    latin_fonts = [p for p in assets if p.name.startswith("inter-latin.")]
    core_fonts = [p for p in assets if p.name.startswith("inter-core.")]
    require(len(latin_fonts) == 1 and latin_fonts[0].stat().st_size <= 256 * 1024, "Latin subset missing or budget exceeded")
    require(len(core_fonts) == 1 and core_fonts[0].stat().st_size <= 48 * 1024, "Critical Latin font missing or budget exceeded")
    require(core_fonts[0].stat().st_size + name_font.stat().st_size < (build / "fonts/InterVariable.woff2").stat().st_size,
            "primary font payload no longer improves on the original Inter asset")
    require((build / "fonts/Inter-OFL.txt").is_file(), "Inter license missing")
    for prefix, vendor_name in [("katex-main.", "KaTeX_Main-Regular.woff2"), ("katex-math-italic.", "KaTeX_Math-Italic.woff2")]:
        matches = [p for p in assets if p.name.startswith(prefix)]
        require(len(matches) == 1, "fingerprinted math font missing")
        require(matches[0].read_bytes() == (build / "vendor/katex/0.19.1/fonts" / vendor_name).read_bytes(),
                "math font differs from approved vendor file")
        require("/assets/" + matches[0].name in css, "CSS does not use fingerprinted math font")

    page_count = 0
    for page_path in build.rglob("*.html"):
        source = page_path.read_text()
        require(not any(marker in source for marker in ("localhost", "data-preview", "name-preview", "font-study", 'content="noindex')),
                f"demo metadata in {page_path.relative_to(build)}")
        parsed = Page(source)
        preloads = []
        for tag, attrs in parsed.elements:
            require(not any(name.lower().startswith("on") for name in attrs), "inline event handler found")
            if tag == "script":
                require(bool(attrs.get("src")), "inline application script found")
                require('/vendor/katex/' not in attrs.get('src',''), "client-side math rendering returned to the loading path")
            reference = attrs.get("src") if tag in {"script", "img"} else attrs.get("href") if tag == "link" else None
            if reference:
                url = urlsplit(reference)
                if not url.netloc and url.path.startswith("/"):
                    target = build / unquote(url.path).lstrip("/")
                    require(target.is_file(), f"missing local resource: {reference}")
                    if attrs.get("integrity"):
                        digest = base64.b64encode(hashlib.sha256(target.read_bytes()).digest()).decode()
                        require(attrs["integrity"] == "sha256-" + digest, f"SRI mismatch: {reference}")
            if tag == "link" and attrs.get("rel") == "preload" and attrs.get("as") == "font":
                require("crossorigin" in attrs and attrs.get("type") == "font/woff2", "font preload mode mismatch")
                require(attrs["href"] in css, "preload URL differs from stylesheet URL")
                preloads.append(attrs["href"])
        if page_path == build / "index.html":
            require(preloads.count("/assets/" + name_font.name) == 1, "homepage needs exactly one name-font preload")
            require(preloads.count("/assets/" + core_fonts[0].name) == 1, "homepage needs exactly one core-font preload")
            require("/assets/" + latin_fonts[0].name not in preloads, "broad Latin font should load only on demand")
            require(len(preloads) == len(set(preloads)), "duplicate font preload")
            require(all(character in source for character in "丁长缨"), "name markup missing")
            require('class="site-home"' in source, "homepage grid class missing")
            require('class="katex"' in source and '<math ' in source, "math must be pre-rendered with accessible MathML")
        else:
            require(not preloads, "non-home page unnecessarily preloads heading fonts")
        page_count += 1

    policies = {}
    route = None
    for raw in (build / "_headers").read_text().splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith((" ", "\t")):
            route = raw.strip()
        elif raw.strip().lower().startswith("cache-control:"):
            require(route not in policies, f"duplicate cache declaration: {route}")
            policies[route] = raw.split(":", 1)[1].strip()
    require("/*" not in policies, "global Cache-Control would overlap asset policies")
    require(policies.get("/assets/*") == "public, max-age=31536000, immutable", "immutable asset policy missing")
    for route in ("/", "/*/", "/*.html"):
        require(policies.get(route) == "public, no-cache", f"HTML revalidation policy missing: {route}")
    for asset in assets:
        url = "/assets/" + asset.name
        require(sum(fnmatch.fnmatchcase(url, pattern) for pattern in policies) == 1, f"overlapping cache rules: {url}")

    compressed_code = sum(len(gzip.compress(p.read_bytes(), mtime=0)) for p in styles + scripts)
    require(compressed_code + name_font.stat().st_size <= 8192, "CSS/JS plus Chinese font exceed 8 KiB budget")
    print(f"PASS: {page_count} HTML pages; resource paths, fingerprints, SRI, licenses, and cache rules verified.")
    print(f"Chinese font: {name_font.stat().st_size:,} bytes; CSS + JS gzip estimate: {compressed_code:,} bytes.")
    if latin_fonts:
        print(f"Inter core: {core_fonts[0].stat().st_size:,} bytes; on-demand broad Latin: {latin_fonts[0].stat().st_size:,} bytes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", nargs="?", type=Path, default=Path("public"))
    check(parser.parse_args().build.resolve())
