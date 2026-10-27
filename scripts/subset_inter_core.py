#!/usr/bin/env python3
"""Build the critical Inter subset without changing its approved rendering.

This is a local maintainer tool, never a Hugo/Cloudflare build step. It reuses
the pinned tool versions and HarfBuzz wrapper in subset_inter_font.py.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# Avoid creating cache files when importing the repository's verification helper.
sys.dont_write_bytecode = True
import subset_inter_font as reference

import brotli
import fontTools
from fontTools import subset
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
REQUESTED = set(range(0x80)) | {
    0x00A0, 0x00A9, 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026,
}
DEFAULT_FEATURES = (
    "calt", "ccmp", "clig", "kern", "liga", "locl", "mark", "mkmk", "rlig", "rvrn",
)
NAMES = {
    1: "Changying Core Sans",
    2: "Regular",
    3: "4.001;git-9221beed3;RSMS;ChangyingCoreSans-Regular",
    4: "Changying Core Sans",
    6: "ChangyingCoreSans",
    16: "Changying Core Sans",
    17: "Regular",
}
SHAPING_LOCATIONS = tuple(
    {"wght": weight, "opsz": optical}
    for weight in (400, 500, 600, 700)
    for optical in (14, 15, 17, 20, 24, 32)
)


def build(source: bytes) -> bytes:
    with TTFont(io.BytesIO(source), recalcTimestamp=False) as font:
        options = subset.Options()
        options.name_IDs = ["*"]
        options.name_languages = ["*"]
        options.layout_features = list(DEFAULT_FEATURES)
        options.glyph_names = True
        options.notdef_outline = True
        options.recalc_timestamp = False
        subsetter = subset.Subsetter(options=options)
        subsetter.populate(unicodes=REQUESTED.intersection(font.getBestCmap()))
        subsetter.subset(font)

        for record in font["name"].names:
            if record.nameID in NAMES:
                value = NAMES[record.nameID]
            elif record.nameID >= 256 and record.toUnicode().startswith("Inter"):
                # This also covers named-instance names, if supplied upstream.
                value = record.toUnicode().replace("InterVariable", "ChangyingCoreSans").replace("Inter", "Changying Core Sans")
            else:
                continue
            record.string = value.encode(record.getEncoding())

        font.flavor = "woff2"
        output = io.BytesIO()
        font.save(output, reorderTables=True)
        return output.getvalue()


class BodyText(HTMLParser):
    """Collect Latin text without treating KaTeX output as Site Sans content."""

    VOID_TAGS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr",
    }
    EXCLUDED_TAGS = {"head", "script", "style", "template", "math", "svg"}
    MATH_CLASSES = {"math", "math-inline", "math-display", "mathjax", "mathjax_display"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool, bool]] = []
        self.texts: list[str] = []
        self.codepoints: set[int] = set()

    def handle_starttag(self, tag: str, attributes: list) -> None:
        attrs = dict(attributes)
        classes = attrs.get("class", "").lower().split()
        inherited_body = self.stack[-1][1] if self.stack else False
        inherited_skip = self.stack[-1][2] if self.stack else False
        skip = inherited_skip or tag in self.EXCLUDED_TAGS or "name-chinese" in classes
        skip = skip or any(
            value.startswith("katex") or value.startswith("mjx-") or value in self.MATH_CLASSES
            for value in classes
        )
        if tag not in self.VOID_TAGS:
            self.stack.append((tag, inherited_body or tag == "body", skip))

    def handle_startendtag(self, tag: str, attributes: list) -> None:
        if tag not in self.VOID_TAGS:
            self.handle_starttag(tag, attributes)
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1][1] or self.stack[-1][2]:
            return
        # Older generated pages contain TeX delimiters; newer ones contain
        # already-rendered .katex subtrees, skipped above. Neither uses Inter.
        data = re.sub(r"\$\$[\s\S]*?\$\$|\$[^$\n]+\$", "", data)
        self.codepoints.update(ord(character) for character in data if ord(character) >= 32)
        normalized = " ".join(data.split())
        if normalized:
            self.texts.append(normalized)


def text_samples(html: str, coverage: set[int]) -> tuple[list[str], set[int]]:
    parser = BodyText()
    parser.feed(html)
    texts = set(parser.texts) | set(reference.TEST_TEXTS) | {
        "© 2026 Changying Ding – a precise heading… “Quotes” and 'apostrophes'.",
    }
    supported = sorted(text for text in texts if all(ord(character) in coverage for character in text))
    return supported, parser.codepoints - coverage


def verify_parser() -> None:
    """Check nested pre-rendered math and raw TeX without needing a browser."""
    sample = """<html><body><h1>Changying Ding<span class="name-chinese">丁长缨</span></h1>
    <p>Raw $\\ell^2$ text.</p><p>Rendered <span class="katex"><span class="katex-mathml">
    <math><mi>ℓ</mi><mn>2</mn><annotation>\\ell^2</annotation></math></span>
    <span class="katex-html"><span>ℓ²</span></span></span> ends here.</p>
    <p>Café</p><script>"Ж"</script><style>.a{content:"字"}</style></body></html>"""
    texts, non_core = text_samples(sample, REQUESTED)
    if non_core != {0x00E9} or "ends here." not in texts or "Raw text." not in texts:
        raise ValueError("Body-text extraction did not correctly exclude math/script/name subtrees.")


def verify_font(source: bytes, result: bytes) -> tuple[set[int], int, int]:
    with TTFont(io.BytesIO(source), recalcTimestamp=False) as original, TTFont(
        io.BytesIO(result), recalcTimestamp=False
    ) as webfont:
        coverage = REQUESTED.intersection(original.getBestCmap())
        if set(webfont.getBestCmap()) != coverage or len(coverage) != 105:
            raise ValueError("Core character coverage must match the approved 105-codepoint subset.")
        for table in ("GDEF", "GPOS", "GSUB", "HVAR", "MVAR", "STAT", "avar", "fvar", "gvar"):
            if table not in webfont:
                raise ValueError(f"Missing shaping/variation table: {table}.")
        if reference.feature_tags(webfont, "GSUB") != {"calt"} or reference.feature_tags(webfont, "GPOS") != {"kern"}:
            raise ValueError("Unexpected applicable core shaping features.")
        for table in ("fvar", "avar", "STAT", "MVAR"):
            if original[table].compile(original) != webfont[table].compile(webfont):
                raise ValueError(f"Axis/global metric data changed: {table}.")

        retained = webfont.getGlyphOrder()
        if len(retained) != 153:
            raise ValueError("Unexpected core glyph count.")
        for name in retained:
            before = [(v.axes, v.coordinates) for v in original["gvar"].variations.get(name, [])]
            after = [(v.axes, v.coordinates) for v in webfont["gvar"].variations.get(name, [])]
            if before != after:
                raise ValueError(f"Variation tuples changed for {name}.")

        outline_checks = 0
        for location in reference.LOCATIONS:
            source_glyphs = original.getGlyphSet(location=location)
            result_glyphs = webfont.getGlyphSet(location=location)
            for name in retained:
                if reference.draw(source_glyphs, name) != reference.draw(result_glyphs, name):
                    raise ValueError(f"Outline changed for {name} at {location}.")
                if source_glyphs[name].width != result_glyphs[name].width:
                    raise ValueError(f"Advance changed for {name} at {location}.")
                outline_checks += 1

        for table, fields in {
            "head": ("unitsPerEm",),
            "hhea": ("ascent", "descent", "lineGap"),
            "OS/2": ("sTypoAscender", "sTypoDescender", "sTypoLineGap", "usWinAscent", "usWinDescent"),
        }.items():
            for field in fields:
                if getattr(original[table], field) != getattr(webfont[table], field):
                    raise ValueError(f"Line metric changed: {table}.{field}.")
        for name_id in (0, 13, 14):
            if original["name"].getDebugName(name_id) != webfont["name"].getDebugName(name_id):
                raise ValueError(f"Copyright/license metadata changed: name ID {name_id}.")
        instance_names = {
            name_id for instance in webfont["fvar"].instances
            for name_id in (instance.subfamilyNameID, instance.postscriptNameID)
            if name_id != 0xFFFF
        }
        for record in webfont["name"].names:
            if record.nameID in {1, 3, 4, 6, 16} | instance_names and "Inter" in record.toUnicode():
                raise ValueError("An original font family name remains in a primary/instance name.")
        if len(result) >= 40_000:
            raise ValueError("Core webfont exceeds its 40 KB budget.")
        return coverage, len(retained), outline_checks


def verify_shaping(source: bytes, result: bytes, library: str, texts: list[str]) -> tuple[str, int]:
    shaper = reference.Shaper(library)
    original = shaper.font(source)
    webfont = shaper.font(result)
    comparisons = 0
    try:
        for location in SHAPING_LOCATIONS:
            for feature in (None, "calt", "kern"):
                for text in texts:
                    if shaper.shape(original, text, location, feature) != shaper.shape(webfont, text, location, feature):
                        raise ValueError(f"Shaping changed at {location}, feature {feature!r}: {text!r}.")
                    comparisons += 1
        return shaper.lib.hb_version_string().decode("ascii"), comparisons
    finally:
        shaper.lib.hb_font_destroy(original[0])
        shaper.lib.hb_font_destroy(webfont[0])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=ROOT / "static/fonts/InterVariable.woff2")
    parser.add_argument("--output", type=Path, default=ROOT / "assets/fonts/inter-core.woff2")
    parser.add_argument("--html", type=Path, default=ROOT / "public/index.html", help="Built homepage used for text/shaping verification")
    parser.add_argument("--harfbuzz-library", default=reference.find_harfbuzz(), help="Path to an existing HarfBuzz shared library")
    args = parser.parse_args()

    if fontTools.__version__ != reference.FONTTOOLS_VERSION or brotli.__version__ != reference.BROTLI_VERSION:
        parser.error("Use the pinned versions in scripts/requirements-fonts.txt.")
    if not args.harfbuzz_library:
        parser.error("A local HarfBuzz library is required; supply --harfbuzz-library.")
    source = args.source.read_bytes()
    if hashlib.sha256(source).hexdigest() != reference.SOURCE_SHA256:
        parser.error("Source checksum differs from the approved Inter Variable 4.001 font.")

    verify_parser()
    result = build(source)
    coverage, glyph_count, outline_checks = verify_font(source, result)
    texts, non_core = text_samples(args.html.read_text(encoding="utf-8"), coverage)
    harfbuzz_version, shaping_checks = verify_shaping(source, result, args.harfbuzz_library, texts)
    if result != build(source):
        raise ValueError("Repeated builds were not byte-identical.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print(json.dumps({
        "output": str(args.output), "bytes": len(result),
        "sha256": hashlib.sha256(result).hexdigest(),
        "source_sha256": reference.SOURCE_SHA256,
        "fonttools": fontTools.__version__, "brotli": brotli.__version__,
        "harfbuzz": harfbuzz_version, "codepoints": len(coverage), "glyphs": glyph_count,
        "outline_advance_checks": outline_checks, "shaping_checks": shaping_checks,
        "text_specimens": len(texts), "deterministic": True,
        "non_core_page_codepoints": [f"U+{value:04X}" for value in sorted(non_core)],
    }, indent=2))
    if non_core:
        print("Non-core page text requires the broad fallback; retest mixed-font shaping and loading.", file=sys.stderr)


if __name__ == "__main__":
    main()
