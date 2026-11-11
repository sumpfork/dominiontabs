from __future__ import print_function

import re
import zlib
from collections import Counter

from domdiv import config_options, main

MM_TO_PT = 72.0 / 25.4

# Small helpers to extract the vector rectangles ("x y w h re" operators)
# from the generated PDFs, so tab sizes can be verified exactly.


def _ascii85_decode(data):
    # reportlab writes streams with /Filter [/ASCII85Decode /FlateDecode]
    data = data.strip()
    if data.endswith(b"~>"):
        data = data[:-2]
    data = data.replace(b"z", b"!!!!")
    if len(data) % 5:
        data += b"~" * (5 - len(data) % 5)
    out = bytearray()
    for i in range(0, len(data), 5):
        value = 0
        for c in data[i : i + 5]:
            value = value * 85 + (c - 33)
        out += value.to_bytes(4, "big")
    return bytes(out)


def _collect_rects(path):
    """Return a Counter of (width_pt, height_pt) for all filled rectangles."""
    rects = Counter()
    data = open(path, "rb").read()
    for match in re.finditer(rb"stream\r?\n", data):
        start = match.end()
        end = data.find(b"endstream", start)
        raw = data[start:end]
        for decoder in (
            zlib.decompress,  # plain Flate
            lambda d: zlib.decompress(_ascii85_decode(d)),  # ASCII85 + Flate
            lambda d: d,  # uncompressed (fallback)
        ):
            try:
                content = decoder(raw)
            except Exception:
                continue
            for r in re.finditer(rb"([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) re\b", content):
                x, y, w, h = (float(v) for v in r.groups())
                if w > 5 and h > 2:  # skip tiny decor rects
                    rects[(round(w, 2), round(h, 2))] += 1
            break
    return rects


def _assert_rect_present(rects, width_mm, height_mm, min_count=1):
    expected_w = width_mm * MM_TO_PT
    expected_h = height_mm * MM_TO_PT
    found = [
        count
        for (w, h), count in rects.items()
        if abs(w - expected_w) < 0.1 and abs(h - expected_h) < 0.1
    ]
    assert sum(found) >= min_count, (
        f"no rectangle of {width_mm}x{height_mm}mm "
        f"({expected_w:.2f}x{expected_h:.2f}pt) found; got {rects.most_common(5)}"
    )


def get_clean_opts(opts, outfile):
    # Pin the paper size so the tests do not depend on the host system's
    # /etc/papersize (which parse_papersize falls back to).
    options = config_options.parse_opts(["--papersize", "LETTER"] + list(opts))
    options = config_options.clean_opts(options)
    options.outfile = str(outfile)
    return options


def test_tab_size_tabs_only(tmp_path):
    # --tabs-only with explicit tab size draws 40x10mm tabs
    outfile = tmp_path / "tabs.pdf"
    options = get_clean_opts(
        [
            "--tabs-only",
            "--black-tabs",
            "--no-tab-artwork",
            "--tabwidth",
            "4.0",
            "--tabheight",
            "1.0",
            "--num-pages",
            "1",
        ],
        outfile,
    )
    main.generate(options)
    rects = _collect_rects(outfile)
    _assert_rect_present(rects, 40, 10, min_count=10)


def test_tab_size_normal(tmp_path):
    # normal dividers draw 40x10mm tabs when tabwidth/tabheight are given
    outfile = tmp_path / "normal.pdf"
    options = get_clean_opts(
        [
            "--black-tabs",
            "--no-tab-artwork",
            "--tabwidth",
            "4.0",
            "--tabheight",
            "1.0",
            "--num-pages",
            "1",
        ],
        outfile,
    )
    main.generate(options)
    rects = _collect_rects(outfile)
    _assert_rect_present(rects, 40, 10, min_count=1)


def test_tab_size_defaults_unchanged(tmp_path):
    # without the options the historic label-based tab size is used
    outfile = tmp_path / "default.pdf"
    options = get_clean_opts(
        ["--tabs-only", "--black-tabs", "--no-tab-artwork", "--num-pages", "1"],
        outfile,
    )
    main.generate(options)
    rects = _collect_rects(outfile)
    _assert_rect_present(rects, 42.5, 10.7, min_count=10)


def test_tab_height_only_overrides_height(tmp_path):
    # only --tabheight given: width stays at the label default
    outfile = tmp_path / "height.pdf"
    options = get_clean_opts(
        [
            "--tabs-only",
            "--black-tabs",
            "--no-tab-artwork",
            "--tabheight",
            "1.0",
            "--num-pages",
            "1",
        ],
        outfile,
    )
    main.generate(options)
    rects = _collect_rects(outfile)
    _assert_rect_present(rects, 42.5, 10, min_count=10)


def test_tab_width_only_overrides_width(tmp_path):
    # only --tabwidth given: height stays at the label default
    outfile = tmp_path / "width.pdf"
    options = get_clean_opts(
        [
            "--tabs-only",
            "--black-tabs",
            "--no-tab-artwork",
            "--tabwidth",
            "5.0",
            "--num-pages",
            "1",
        ],
        outfile,
    )
    main.generate(options)
    rects = _collect_rects(outfile)
    _assert_rect_present(rects, 50, 10.7, min_count=1)


def test_explicit_tabwidth_prevents_full_tab_side():
    # an explicit --tabwidth must not let the label force --tab-side=full,
    # otherwise the width would be ignored in tabs-only mode
    options = config_options.parse_opts(["--tabs-only", "--tabwidth", "4.0"])
    options = config_options.clean_opts(options)
    assert options.tab_side != "full"

    options = config_options.parse_opts(["--tabs-only"])
    options = config_options.clean_opts(options)
    assert options.tab_side == "full"  # default Avery 8867 is narrow
