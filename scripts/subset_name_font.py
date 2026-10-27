#!/usr/bin/env python3
"""Build the checked-in, three-character WOFF2 used by the bilingual heading.

This is a maintainer tool, not part of the Hugo/Cloudflare build. See
docs/font-build.md for the upstream download and pinned Python environment.
"""

from __future__ import annotations

import argparse
import hashlib
import io
from pathlib import Path

import brotli
import fontTools
from fontTools import subset
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont


TEXT = "丁长缨"
UNICODES = {ord(character) for character in TEXT}
SOURCE_SHA256 = "558c62730844fe54ba220146ed62f859d4e2880188d92d985f8921c6e3743bc4"
FONTTOOLS_VERSION = "4.60.2"
BROTLI_VERSION = "1.2.0"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "assets/fonts/zhuque-name.woff2"
SUBSET_NAMES = {
    1: "Changying Name Serif",
    2: "Regular",
    3: "0.212;TRIO;ChangyingNameSerif-Regular",
    4: "Changying Name Serif Regular",
    6: "ChangyingNameSerif-Regular",
    16: "Changying Name Serif",
    17: "Regular",
}


def build(source: bytes) -> bytes:
    """Keep the original glyph geometry, hinting, metrics, and license metadata."""
    with TTFont(io.BytesIO(source), recalcTimestamp=False) as font:
        options = subset.Options()
        options.name_IDs = ["*"]
        options.name_languages = ["*"]
        options.layout_features = ["*"]
        options.glyph_names = True
        options.notdef_outline = True
        options.recalc_timestamp = False
        subsetter = subset.Subsetter(options=options)
        subsetter.populate(unicodes=UNICODES)
        subsetter.subset(font)

        # Identify the derivative separately; copyright and licensing records
        # remain those supplied by the font's original authors.
        for record in font["name"].names:
            if record.nameID in SUBSET_NAMES:
                record.string = SUBSET_NAMES[record.nameID].encode(record.getEncoding())

        font.flavor = "woff2"
        output = io.BytesIO()
        font.save(output, reorderTables=True)
        return output.getvalue()


def outline(font: TTFont, glyph_name: str) -> list:
    glyphs = font.getGlyphSet()
    pen = DecomposingRecordingPen(glyphs)
    glyphs[glyph_name].draw(pen)
    return pen.value


def verify(source: bytes, result: bytes) -> None:
    """Check the decoded webfont, rather than only its pre-compression object."""
    with TTFont(io.BytesIO(source), recalcTimestamp=False) as original, TTFont(
        io.BytesIO(result), recalcTimestamp=False
    ) as webfont:
        source_cmap = original.getBestCmap()
        result_cmap = webfont.getBestCmap()
        if set(result_cmap) != UNICODES:
            raise ValueError("The webfont cmap must contain exactly 丁长缨.")
        for codepoint in sorted(UNICODES):
            source_glyph = source_cmap[codepoint]
            result_glyph = result_cmap[codepoint]
            if outline(original, source_glyph) != outline(webfont, result_glyph):
                raise ValueError(f"Outline changed for U+{codepoint:04X}.")
            if original["hmtx"][source_glyph] != webfont["hmtx"][result_glyph]:
                raise ValueError(f"Horizontal metrics changed for U+{codepoint:04X}.")

        metric_fields = {
            "head": ("unitsPerEm",),
            "hhea": ("ascent", "descent", "lineGap"),
            "OS/2": (
                "sTypoAscender", "sTypoDescender", "sTypoLineGap",
                "usWinAscent", "usWinDescent",
            ),
        }
        for table, fields in metric_fields.items():
            for field in fields:
                if getattr(original[table], field) != getattr(webfont[table], field):
                    raise ValueError(f"Font metric changed: {table}.{field}.")
        for name_id in (0, 13, 14):
            if original["name"].getDebugName(name_id) != webfont["name"].getDebugName(name_id):
                raise ValueError(f"Copyright/license metadata changed: name ID {name_id}.")
        if len(result) >= 10_000:
            raise ValueError("Unexpected webfont size: expected less than 10 KB.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Original ZhuqueFangsong-Regular.ttf v0.212")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if fontTools.__version__ != FONTTOOLS_VERSION or brotli.__version__ != BROTLI_VERSION:
        parser.error("Use the pinned versions in scripts/requirements-fonts.txt for reproducibility.")
    source = args.source.read_bytes()
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        parser.error("Source checksum differs from the approved Zhuque Fangsong v0.212 font.")

    result = build(source)
    verify(source, result)
    if result != build(source):
        raise ValueError("Repeated builds were not byte-for-byte identical.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print(f"Wrote {args.output}: {len(result):,} bytes")
    print(f"SHA-256: {hashlib.sha256(result).hexdigest()}")
    print("Verified exact cmap, original outlines/metrics/license metadata, and deterministic output.")


if __name__ == "__main__":
    main()
