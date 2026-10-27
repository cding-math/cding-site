#!/usr/bin/env python3
"""Build and verify the variable Latin Inter subset; not a Cloudflare build step.

Requires pinned scripts/requirements-fonts.txt tools plus a local HarfBuzz shared
library for source/subset shaping comparisons. See docs/inter-font-build.md.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import hashlib
import io
from pathlib import Path

import brotli
import fontTools
from fontTools import subset
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA256 = "693b77d4f32ee9b8bfc995589b5fad5e99adf2832738661f5402f9978429a8e3"
FONTTOOLS_VERSION = "4.60.2"
BROTLI_VERSION = "1.2.0"
RANGES = (
    (0x0000, 0x024F), (0x0300, 0x036F), (0x1E00, 0x1EFF),
    (0x2000, 0x206F), (0x20A0, 0x20CF), (0x2190, 0x2199),
)
REQUESTED = {cp for start, end in RANGES for cp in range(start, end + 1)} | {
    0x2113, 0x2122, 0x2212, 0xFEFF, 0xFFFD,
}
NAMES = {
    1: "Changying Latin Sans",
    2: "Regular",
    3: "4.001;git-9221beed3;RSMS;ChangyingLatinSans-Regular",
    4: "Changying Latin Sans",
    6: "ChangyingLatinSans",
    16: "Changying Latin Sans",
    17: "Regular",
}
TEST_TEXTS = (
    "Changying Ding",
    "I am a Lecturer in Mathematics at UCLA, where I was a Hedrick Math Fellow from 2023 to 2026.",
    "My CV is available here, and my research is supported in part by NSF grant DMS-2554483.",
    "Publications / Preprints: Structural and non-isomorphism results for von Neumann algebras.",
    "AVATAR To WA Yo fi fl ff ffi ffl 0123456789 1/2 3/4 (CASE) @ $ £ € − → ™",
    "Café naïve Ångström Śląsk Český ǅ Ắ A\u030a e\u0301 n\u0303 a\u0308\u0301",
    "abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789 !?:;.,-–—()[]{}",
)
LOCATIONS = tuple(
    {"wght": weight, "opsz": optical}
    for weight in (400, 500, 600)
    for optical in (14, 32)
)


def build(source: bytes) -> bytes:
    with TTFont(io.BytesIO(source), recalcTimestamp=False) as font:
        options = subset.Options()
        options.name_IDs = ["*"]
        options.name_languages = ["*"]
        options.layout_features = ["*"]
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
                value = record.toUnicode().replace("InterVariable", "ChangyingLatinSans").replace("Inter", "Changying Latin Sans")
            else:
                continue
            record.string = value.encode(record.getEncoding())
        font.flavor = "woff2"
        output = io.BytesIO()
        font.save(output, reorderTables=True)
        return output.getvalue()


def feature_tags(font: TTFont, table: str) -> set[str]:
    return {record.FeatureTag for record in font[table].table.FeatureList.FeatureRecord}


def draw(glyphs, name: str) -> list:
    pen = DecomposingRecordingPen(glyphs)
    glyphs[name].draw(pen)
    return pen.value


def verify_font(source: bytes, result: bytes) -> tuple[int, int, set[str]]:
    with TTFont(io.BytesIO(source), recalcTimestamp=False) as original, TTFont(
        io.BytesIO(result), recalcTimestamp=False
    ) as webfont:
        expected = REQUESTED.intersection(original.getBestCmap())
        if set(webfont.getBestCmap()) != expected:
            raise ValueError("The subset Unicode coverage does not match the requested source coverage.")
        for text in TEST_TEXTS:
            if any(ord(character) not in expected for character in text):
                raise ValueError("A shaping specimen contains an unsupported character.")

        for table in ("GDEF", "GPOS", "GSUB", "HVAR", "MVAR", "STAT", "avar", "fvar", "gvar"):
            if table not in webfont:
                raise ValueError(f"Missing shaping/variation table: {table}.")
        for table in ("GSUB", "GPOS"):
            if feature_tags(original, table) != feature_tags(webfont, table):
                raise ValueError(f"OpenType feature tags changed: {table}.")
        for table in ("fvar", "avar", "STAT", "MVAR"):
            if original[table].compile(original) != webfont[table].compile(webfont):
                raise ValueError(f"Axis/instance/global metric table changed: {table}.")

        retained = webfont.getGlyphOrder()
        for name in retained:
            before = original["gvar"].variations.get(name, [])
            after = webfont["gvar"].variations.get(name, [])
            if [(v.axes, v.coordinates) for v in before] != [(v.axes, v.coordinates) for v in after]:
                raise ValueError(f"Variation tuples changed for {name}.")

        for location in LOCATIONS:
            source_glyphs = original.getGlyphSet(location=location)
            result_glyphs = webfont.getGlyphSet(location=location)
            for name in retained:
                if draw(source_glyphs, name) != draw(result_glyphs, name):
                    raise ValueError(f"Outline changed for {name} at {location}.")
                if source_glyphs[name].width != result_glyphs[name].width:
                    raise ValueError(f"Advance changed for {name} at {location}.")

        for name_id in (0, 13, 14):
            if original["name"].getDebugName(name_id) != webfont["name"].getDebugName(name_id):
                raise ValueError(f"Copyright/license metadata changed: name ID {name_id}.")
        for table, fields in {
            "head": ("unitsPerEm",),
            "hhea": ("ascent", "descent", "lineGap"),
            "OS/2": ("sTypoAscender", "sTypoDescender", "sTypoLineGap", "usWinAscent", "usWinDescent"),
        }.items():
            for field in fields:
                if getattr(original[table], field) != getattr(webfont[table], field):
                    raise ValueError(f"Line metric changed: {table}.{field}.")
        if len(result) > 256_000:
            raise ValueError("Latin font exceeds the 256 KB budget.")
        return len(expected), len(retained), feature_tags(original, "GSUB") | feature_tags(original, "GPOS")


class GlyphInfo(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in ("codepoint", "mask", "cluster", "var1", "var2")]


class GlyphPosition(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int32) for name in ("x_advance", "y_advance", "x_offset", "y_offset", "var")]


class Variation(ctypes.Structure):
    _fields_ = [("tag", ctypes.c_uint32), ("value", ctypes.c_float)]


class Feature(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in ("tag", "value", "start", "end")]


def tag(value: str) -> int:
    return int.from_bytes(value.encode("ascii"), "big")


class Shaper:
    """Small wrapper around the installed HarfBuzz C API; no font installation."""

    def __init__(self, library: str):
        self.lib = ctypes.CDLL(library)
        signatures = {
            "hb_version_string": (ctypes.c_char_p, []),
            "hb_blob_create": (ctypes.c_void_p, [ctypes.c_char_p, ctypes.c_uint, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]),
            "hb_blob_destroy": (None, [ctypes.c_void_p]),
            "hb_face_create": (ctypes.c_void_p, [ctypes.c_void_p, ctypes.c_uint]),
            "hb_face_destroy": (None, [ctypes.c_void_p]),
            "hb_font_create": (ctypes.c_void_p, [ctypes.c_void_p]),
            "hb_font_destroy": (None, [ctypes.c_void_p]),
            "hb_ot_font_set_funcs": (None, [ctypes.c_void_p]),
            "hb_font_set_variations": (None, [ctypes.c_void_p, ctypes.POINTER(Variation), ctypes.c_uint]),
            "hb_buffer_create": (ctypes.c_void_p, []),
            "hb_buffer_destroy": (None, [ctypes.c_void_p]),
            "hb_buffer_add_utf8": (None, [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_uint, ctypes.c_int]),
            "hb_buffer_guess_segment_properties": (None, [ctypes.c_void_p]),
            "hb_shape": (None, [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(Feature), ctypes.c_uint]),
            "hb_buffer_get_glyph_infos": (ctypes.POINTER(GlyphInfo), [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]),
            "hb_buffer_get_glyph_positions": (ctypes.POINTER(GlyphPosition), [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]),
        }
        for name, (result, arguments) in signatures.items():
            function = getattr(self.lib, name)
            function.restype = result
            function.argtypes = arguments

    def font(self, data: bytes):
        with TTFont(io.BytesIO(data), recalcTimestamp=False) as font:
            order = font.getGlyphOrder()
            font.flavor = None
            sfnt = io.BytesIO()
            font.save(sfnt, reorderTables=True)
        data = sfnt.getvalue()
        blob = self.lib.hb_blob_create(data, len(data), 0, None, None)  # Duplicate data.
        face = self.lib.hb_face_create(blob, 0)
        handle = self.lib.hb_font_create(face)
        self.lib.hb_ot_font_set_funcs(handle)
        self.lib.hb_face_destroy(face)
        self.lib.hb_blob_destroy(blob)
        return handle, order

    def shape(self, font, text: str, location: dict, enabled: str | None) -> list:
        handle, order = font
        variations = (Variation * len(location))(*(Variation(tag(k), v) for k, v in location.items()))
        self.lib.hb_font_set_variations(handle, variations, len(variations))
        features = (Feature * (1 if enabled else 0))(*([Feature(tag(enabled), 1, 0, 0xFFFFFFFF)] if enabled else []))
        buffer = self.lib.hb_buffer_create()
        try:
            encoded = text.encode("utf-8")
            self.lib.hb_buffer_add_utf8(buffer, encoded, len(encoded), 0, len(encoded))
            self.lib.hb_buffer_guess_segment_properties(buffer)
            self.lib.hb_shape(handle, buffer, features, len(features))
            count = ctypes.c_uint()
            infos = self.lib.hb_buffer_get_glyph_infos(buffer, ctypes.byref(count))
            positions = self.lib.hb_buffer_get_glyph_positions(buffer, ctypes.byref(count))
            return [
                (order[infos[i].codepoint], infos[i].cluster, positions[i].x_advance,
                 positions[i].y_advance, positions[i].x_offset, positions[i].y_offset)
                for i in range(count.value)
            ]
        finally:
            self.lib.hb_buffer_destroy(buffer)


def find_harfbuzz() -> str | None:
    library = ctypes.util.find_library("harfbuzz")
    if library:
        return library
    # Pillow's macOS wheel can provide HarfBuzz even when RAQM is unavailable.
    try:
        import PIL
        bundled = Path(PIL.__file__).parent / ".dylibs/libharfbuzz.0.dylib"
        if bundled.is_file():
            return str(bundled)
    except ImportError:
        pass
    return None


def verify_shaping(source: bytes, result: bytes, library: str, features: set[str]) -> tuple[str, int]:
    shaper = Shaper(library)
    original = shaper.font(source)
    subset_font = shaper.font(result)
    comparisons = 0
    try:
        locations = LOCATIONS + ({"wght": 500, "opsz": 17}, {"wght": 600, "opsz": 20}, {"wght": 400, "opsz": 24})
        for location in locations:
            for feature in [None] + sorted(features):
                for text in TEST_TEXTS:
                    if shaper.shape(original, text, location, feature) != shaper.shape(subset_font, text, location, feature):
                        raise ValueError(f"Shaping differs at {location}, feature {feature!r}: {text!r}.")
                    comparisons += 1
        return shaper.lib.hb_version_string().decode("ascii"), comparisons
    finally:
        shaper.lib.hb_font_destroy(original[0])
        shaper.lib.hb_font_destroy(subset_font[0])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Original checked-in InterVariable.woff2")
    parser.add_argument("--output", type=Path, default=ROOT / "assets/fonts/inter-latin.woff2")
    parser.add_argument("--harfbuzz-library", default=find_harfbuzz(), help="Path to an existing HarfBuzz shared library")
    args = parser.parse_args()
    if fontTools.__version__ != FONTTOOLS_VERSION or brotli.__version__ != BROTLI_VERSION:
        parser.error("Use the pinned versions in scripts/requirements-fonts.txt.")
    if not args.harfbuzz_library:
        parser.error("A local HarfBuzz library is required; supply --harfbuzz-library.")
    source = args.source.read_bytes()
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        parser.error("Source checksum differs from the approved Inter Variable 4.001 font.")
    result = build(source)
    coverage, glyph_count, features = verify_font(source, result)
    harfbuzz_version, comparisons = verify_shaping(source, result, args.harfbuzz_library, features)
    if result != build(source):
        raise ValueError("Repeated builds were not byte-identical.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print(f"Wrote {args.output}: {len(result):,} bytes")
    print(f"SHA-256: {hashlib.sha256(result).hexdigest()}")
    print(f"Verified {coverage} encoded characters, {glyph_count} glyphs, all feature tags and variable axes.")
    print(f"Verified outlines/advances at {len(LOCATIONS)} instances and {comparisons} shaping comparisons (HarfBuzz {harfbuzz_version}).")
    print("Repeated build is byte-identical; original copyright/license metadata retained.")


if __name__ == "__main__":
    main()
