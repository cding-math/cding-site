# Chinese heading font

The approved Chinese typeface is **朱雀仿宋 / Zhuque Fangsong Regular v0.212**.
The production asset is a WOFF2 subset containing only **丁长缨**:
U+4E01, U+957F, and U+7F28. Its internal family name is **Changying Name Serif**,
to identify this derivative separately from the full upstream typeface.

## Provenance and license

- Project: <https://github.com/TrionesType/zhuque>
- Release: <https://github.com/TrionesType/zhuque/releases/tag/v0.212>
- Official archive: <https://github.com/TrionesType/zhuque/releases/download/v0.212/ZhuqueFangsong-v0.212.zip>
- Input file inside that archive: `ZhuqueFangsong-Regular.ttf`.
- Input size: **8,824,084 bytes**.
- Input SHA-256: `558c62730844fe54ba220146ed62f859d4e2880188d92d985f8921c6e3743bc4`.
- License: SIL Open Font License 1.1; retained at
  `static/fonts/ZhuqueFangsong-OFL.txt`, alongside the distributed webfont.
- The original copyright and license metadata are also retained inside WOFF2.

The full font and other experimental fonts are not needed in the production
repository. The subset changes character coverage and internal naming, not the
three selected glyphs' outlines, horizontal advances, or font line metrics.

## Checked-in artifact

- File: `assets/fonts/zhuque-name.woff2`.
- Size: **2,572 bytes** (about 2.51 KiB; more than 99.97% smaller than the TTF).
- SHA-256: `ad7da318c3146b76061aa24fe89f05fa12c8dd1bd627998072ca29bab09314a2`.
- Encoded glyphs: `.notdef`, `uni4E01`, `uni7F28`, and `uni957F`.

Hugo consumes this already-built artifact. **Cloudflare builds must not download
the upstream font, install Python packages, or regenerate the subset.** The
website build can fingerprint the asset for cache-safe URLs without a font toolchain.

## Rebuild locally

Use Python 3 with the pinned FontTools 4.60.2 and Brotli 1.2.0 versions. Keep the
environment and downloaded upstream files outside the repository, or explicitly
ignore them. For example, using a temporary directory you control:

```sh
python3 -m venv /tmp/cding-font-build
/tmp/cding-font-build/bin/python -m pip install -r scripts/requirements-fonts.txt
/tmp/cding-font-build/bin/python scripts/subset_name_font.py /path/to/ZhuqueFangsong-Regular.ttf
```

The output defaults to `assets/fonts/zhuque-name.woff2`. An optional `--output`
argument permits a second build for comparison without replacing that file.

The script refuses a different upstream checksum or tool version, preserves
source timestamps, fixes table order, and verifies two independent builds are
byte-for-byte identical. After decoding the WOFF2, it checks:

1. The Unicode cmap contains exactly the three requested characters.
2. Each decomposed glyph outline and horizontal metric matches upstream.
3. Units per em, ascender/descender, line gap, and Windows line metrics match.
4. Copyright and license metadata remain unchanged.
5. The result remains below 10 KB.

Changing the Chinese name requires updating both its markup and this subset's
character list, then reviewing its rendering. Changing the upstream font version
also requires deliberately updating the source checksum, provenance, artifact
hash, and design review; do not silently accept an arbitrary input font.
