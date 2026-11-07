#!/usr/bin/env python3
"""Build the project report (.docx) from the Markdown files in ``report/sections/``.

Input:  every ``*.md`` file of the sections directory (``README.md`` excluded), read in
        file-name order and written with the Markdown conventions listed in
        ``report/build/README.md`` (cover, chapters, figures, tables, citations...).
Output: one Word document (default ``report/bao-cao.docx``) plus a summary and the list of
        warnings printed on stdout.

Exit codes: 0 = written (warnings allowed), 1 = warnings with ``--strict``,
2 = input error (no sections directory / no Markdown file), 3 = cannot write the output.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from docx import Document
from docx.document import Document as DocxDocument
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.image.image import Image as DocxImage
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

# ---------------------------------------------------------------------------
# Page layout and typography (defaults; edit here or pass CLI options)
# ---------------------------------------------------------------------------
PAGE_WIDTH_CM = 21.0  # A4
PAGE_HEIGHT_CM = 29.7
MARGIN_LEFT_CM = 3.0
MARGIN_RIGHT_CM = 2.0
MARGIN_TOP_CM = 2.0
MARGIN_BOTTOM_CM = 2.0
FONT_NAME = "Times New Roman"
CODE_FONT_NAME = "Consolas"
BODY_SIZE_PT = 13
LINE_SPACING = 1.3
FIRST_LINE_INDENT_CM = 1.0
PARAGRAPH_SPACE_AFTER_PT = 6
HEADING_SIZES_PT = {1: 16, 2: 14, 3: 13, 4: 13}
CAPTION_SIZE_PT = 12
TABLE_SIZE_PT = 11
SOURCE_SIZE_PT = 11
CODE_SIZE_PT = 10
CODE_SHADING_HEX = "F2F2F2"
IMAGE_MAX_WIDTH_CM = 16.0
# Leave room for the caption below the picture on the same page.
IMAGE_CAPTION_RESERVE_CM = 4.0
COVER_IMAGE_MAX_HEIGHT_CM = 6.0
LIST_INDENT_CM = 1.5
LIST_LEVEL_STEP_CM = 0.75
LIST_HANGING_CM = 0.6

DEFAULT_AUTHOR = "Huỳnh Ngọc Trúc"
FIGURE_WORD = "Hình"
TABLE_WORD = "Bảng"
TOC_HINT = "Nhấn chuột phải → Update Field để cập nhật mục lục"
LIST_HINT = "Nhấn chuột phải → Update Field để cập nhật danh mục và số trang"
RED = RGBColor(0xFF, 0x00, 0x00)
BLACK = RGBColor(0x00, 0x00, 0x00)
GREY = RGBColor(0x59, 0x59, 0x59)

EXIT_OK = 0
EXIT_STRICT_WARNINGS = 1
EXIT_INPUT_ERROR = 2
EXIT_OUTPUT_ERROR = 3

REPO_ROOT_DEFAULT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Seg:
    """One inline piece of text with its formatting or meaning."""

    kind: str  # text | code | cite | xref
    text: str = ""
    bold: bool = False
    italic: bool = False
    highlight: bool = False
    keys: tuple[str, ...] = ()  # cite
    ref: str = ""  # xref, e.g. "fig:arch"


@dataclass
class ListItem:
    """One list item; ``level`` is 0 or 1."""

    level: int
    ordered: bool
    number: int
    segs: list[Seg]


@dataclass
class Block:
    """One block-level element of the Markdown document."""

    kind: str  # heading|para|list|code|figure|table|table_caption|source|refdef|cover|blank|image
    loc: str
    level: int = 0
    segs: list[Seg] = field(default_factory=list)
    text: str = ""  # code text, image path, refdef key
    label: str = ""  # "fig:x" / "tbl:x"
    items: list[ListItem] = field(default_factory=list)
    header: list[list[Seg]] = field(default_factory=list)
    rows: list[list[list[Seg]]] = field(default_factory=list)
    aligns: list[str] = field(default_factory=list)
    caption: list[Seg] | None = None
    children: list[Block] = field(default_factory=list)
    number: str = ""  # assigned figure/table number, e.g. "2.3"
    attached_to: str = ""  # for a source line: "figure" or "table"


class Warnings:
    """Collects non-fatal problems so the build can continue."""

    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, loc: str, message: str) -> None:
        """Record one warning located at ``loc`` (``file:line``)."""
        self.items.append(f"{loc}: {message}" if loc else message)


class ReportInputError(Exception):
    """Raised when the input cannot be read at all (no sections, no Markdown)."""


@dataclass
class BuildResult:
    """Summary of one build."""

    output: Path
    title: str
    chapters: int
    other_level1: int
    figures: int
    missing_images: int
    tables: int
    unnumbered_tables: int
    citation_uses: int
    cited_sources: int
    references: int
    warnings: list[str]


# ---------------------------------------------------------------------------
# Inline parsing
# ---------------------------------------------------------------------------
ESCAPABLE = set("\\`*_[]@|{}#")
ESC_BASE = 0xE000  # private-use code points standing for escaped characters
CODE_BASE = 0xF000  # private-use code points standing for code spans
CODE_PLACEHOLDER_RE = re.compile("([-])")

_KEY = r"@[\w.:/\-]+"
INLINE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("missing", re.compile(r"\[\s*CHƯA CÓ\s*:(.*?)\]", re.DOTALL)),
    ("cite", re.compile(r"\[\s*(" + _KEY + r"(?:\s*[;,]\s*" + _KEY + r")*)\s*\]")),
    ("bold", re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", re.DOTALL)),
    ("italic", re.compile(r"\*(?=[^\s*])(.+?)(?<=[^\s*])\*", re.DOTALL)),
    ("xref", re.compile(r"(?<![\w@])@(fig|tbl):([\w\-]*\w)")),
]


def _protect(text: str) -> tuple[str, list[str]]:
    """Replace backslash escapes and code spans by private-use placeholders."""
    codes: list[str] = []
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "\\" and i + 1 < n and text[i + 1] in ESCAPABLE:
            out.append(chr(ESC_BASE + ord(text[i + 1])))
            i += 2
            continue
        if ch == "`":
            j = i
            while j < n and text[j] == "`":
                j += 1
            ticks = text[i:j]
            end = text.find(ticks, j)
            # The closing run must have exactly the same length as the opening one.
            while end != -1 and end + len(ticks) < n and text[end + len(ticks)] == "`":
                k = end
                while k < n and text[k] == "`":
                    k += 1
                end = text.find(ticks, k)
            if end == -1:
                out.append(ticks)
                i = j
                continue
            content = text[j:end]
            if len(content) >= 2 and content[0] == " " and content[-1] == " " and content.strip():
                content = content[1:-1]
            out.append(chr(CODE_BASE + len(codes)))
            codes.append(content)
            i = end + len(ticks)
            continue
        out.append(ch)
        i += 1
    return "".join(out), codes


def _unescape(text: str) -> str:
    """Turn escape placeholders back into their literal characters."""
    return "".join(
        chr(ord(c) - ESC_BASE) if ESC_BASE <= ord(c) < ESC_BASE + 128 else c for c in text
    )


def _emit_text(
    text: str, codes: list[str], bold: bool, italic: bool, highlight: bool, out: list[Seg]
) -> None:
    for piece in CODE_PLACEHOLDER_RE.split(text):
        if not piece:
            continue
        if len(piece) == 1 and CODE_BASE <= ord(piece) < CODE_BASE + 0x800:
            out.append(Seg("code", codes[ord(piece) - CODE_BASE], bold, italic, highlight))
        else:
            out.append(Seg("text", _unescape(piece), bold, italic, highlight))


def _parse_rich(
    text: str, codes: list[str], bold: bool, italic: bool, highlight: bool, out: list[Seg]
) -> None:
    pos = 0
    while pos < len(text):
        best: tuple[str, re.Match[str]] | None = None
        for kind, regex in INLINE_PATTERNS:
            match = regex.search(text, pos)
            # Strict "<" keeps the earlier pattern of the list on ties (priority order).
            if match and (best is None or match.start() < best[1].start()):
                best = (kind, match)
        if best is None:
            break
        kind, match = best
        if match.start() > pos:
            _emit_text(text[pos : match.start()], codes, bold, italic, highlight, out)
        if kind == "missing":
            _emit_text(text[match.start() : match.start(1)], codes, bold, italic, True, out)
            _parse_rich(match.group(1), codes, bold, italic, True, out)
            _emit_text(text[match.end(1) : match.end()], codes, bold, italic, True, out)
        elif kind == "cite":
            keys = tuple(k.strip()[1:] for k in re.split(r"[;,]", match.group(1)))
            out.append(Seg("cite", _unescape(match.group(0)), bold, italic, highlight, keys=keys))
        elif kind == "bold":
            _parse_rich(match.group(1), codes, True, italic, highlight, out)
        elif kind == "italic":
            _parse_rich(match.group(1), codes, bold, True, highlight, out)
        else:  # xref
            ref = f"{match.group(1)}:{match.group(2)}"
            out.append(Seg("xref", match.group(0), bold, italic, highlight, ref=ref))
        pos = match.end()
    if pos < len(text):
        _emit_text(text[pos:], codes, bold, italic, highlight, out)


def parse_inline(text: str) -> list[Seg]:
    """Parse inline Markdown (bold, italic, code, citations, cross-references, CHƯA CÓ)."""
    protected, codes = _protect(text)
    segs: list[Seg] = []
    _parse_rich(protected, codes, False, False, False, segs)
    return segs


# ---------------------------------------------------------------------------
# Block parsing
# ---------------------------------------------------------------------------
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w+\-.]*)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")
REFDEF_RE = re.compile(r"^\[@([^\]\s]+)\]:\s*(.*)$")
FIGURE_RE = re.compile(
    r"^!\[(?P<cap>.*)\]\((?P<path>[^)\s]+)(?:\s+\"[^\"]*\")?\)\s*"
    r"(?:\{\s*#(?P<label>fig:[\w\-]+)\s*\})?\s*$"
)
TABLE_CAPTION_RE = re.compile(r"^Bảng:\s*(?P<cap>.*?)\s*(?:\{\s*#(?P<label>tbl:[\w\-]+)\s*\})?\s*$")
SOURCE_RE = re.compile(r"^Nguồn\s*:")
LIST_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<marker>[-*+]|\d{1,9}[.)])\s+(?P<text>.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
HR_RE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
CHAPTER_RE = re.compile(r"^\s*Chương\s+(\d+|[IVXLC]+)\b", re.IGNORECASE)
APPENDIX_RE = re.compile(r"^\s*Phụ\s+lục\s+([A-Z0-9]+)\b", re.IGNORECASE)
COVER_TITLES = {"BÌA", "TRANG BÌA"}


def strip_html_comments(text: str, name: str, warnings: Warnings) -> str:
    """Drop ``<!-- ... -->`` comments, keeping line numbers stable."""
    text = COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    start = text.find("<!--")
    if start != -1:
        line = text.count("\n", 0, start) + 1
        warnings.add(
            f"{name}:{line}", "chú thích HTML '<!--' không có '-->'; bỏ phần còn lại của file"
        )
        text = text[:start]
    return text


def _split_row(line: str) -> list[str]:
    """Split one pipe-table row into raw cell strings (honours ``\\|`` and code spans)."""
    s = line.strip()
    s = s.removeprefix("|")
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            current.append("\\|")
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    cells.append("".join(current).strip())
    return cells


def _align_of(spec: str) -> str:
    spec = spec.strip()
    if spec.startswith(":") and spec.endswith(":"):
        return "center"
    if spec.endswith(":"):
        return "right"
    return "left"


class MarkdownFileParser:
    """Line-based parser for one section file."""

    def __init__(self, name: str, text: str, warnings: Warnings) -> None:
        self.name = name
        self.lines = text.split("\n")
        self.warnings = warnings

    def loc(self, index: int) -> str:
        """Return ``file:line`` for a 0-based line index."""
        return f"{self.name}:{index + 1}"

    # -- helpers -----------------------------------------------------------
    def _is_table_start(self, i: int) -> bool:
        if i + 1 >= len(self.lines) or "|" not in self.lines[i]:
            return False
        sep = self.lines[i + 1]
        return "|" in sep and "-" in sep and bool(TABLE_SEP_RE.match(sep))

    def _starts_block(self, i: int) -> bool:
        line = self.lines[i]
        stripped = line.strip()
        if FENCE_RE.match(line) or HEADING_RE.match(line) or REFDEF_RE.match(line):
            return True
        if FIGURE_RE.match(stripped) or TABLE_CAPTION_RE.match(stripped):
            return True
        if SOURCE_RE.match(stripped) or self._is_table_start(i):
            return True
        list_match = LIST_RE.match(line)
        if list_match:
            marker = list_match.group("marker")
            return not marker[0].isdigit() or marker[:-1] == "1"
        return False

    # -- main loop -----------------------------------------------------------
    def parse(self) -> list[Block]:
        """Return the blocks of the file in order."""
        blocks: list[Block] = []
        lines = self.lines
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if not stripped:
                i += 1
                continue
            fence = FENCE_RE.match(line)
            if fence:
                i = self._code(i, fence.group(1), blocks)
                continue
            heading = HEADING_RE.match(line)
            if heading:
                level, title = len(heading.group(1)), heading.group(2)
                if level == 1 and title.strip().upper() in COVER_TITLES:
                    i = self._cover(i, blocks)
                    continue
                if level > 4:
                    self.warnings.add(self.loc(i), f"tiêu đề cấp {level} được dựng như cấp 4")
                    level = 4
                blocks.append(Block("heading", self.loc(i), level=level, segs=parse_inline(title)))
                i += 1
                continue
            refdef = REFDEF_RE.match(line)
            if refdef:
                i = self._refdef(i, refdef, blocks)
                continue
            figure = FIGURE_RE.match(stripped)
            if figure:
                blocks.append(
                    Block(
                        "figure",
                        self.loc(i),
                        segs=parse_inline(figure.group("cap").strip()),
                        text=figure.group("path"),
                        label=figure.group("label") or "",
                    )
                )
                i += 1
                continue
            caption = TABLE_CAPTION_RE.match(stripped)
            if caption:
                blocks.append(
                    Block(
                        "table_caption",
                        self.loc(i),
                        segs=parse_inline(caption.group("cap")),
                        label=caption.group("label") or "",
                        text=stripped,
                    )
                )
                i += 1
                continue
            if self._is_table_start(i):
                i = self._table(i, blocks)
                continue
            if SOURCE_RE.match(stripped):
                blocks.append(Block("source", self.loc(i), segs=parse_inline(stripped)))
                i += 1
                continue
            if LIST_RE.match(line):
                i = self._list(i, blocks)
                continue
            if HR_RE.match(line):
                self.warnings.add(self.loc(i), "đường kẻ ngang chưa được hỗ trợ; đã bỏ qua")
                i += 1
                continue
            if stripped.startswith(">"):
                self.warnings.add(
                    self.loc(i), "trích khối '>' chưa được hỗ trợ; dựng như đoạn thường"
                )
            elif stripped.startswith("<") and re.match(r"<[A-Za-z/]", stripped):
                self.warnings.add(self.loc(i), "thẻ HTML chưa được hỗ trợ; giữ nguyên chữ")
            i = self._paragraph(i, blocks)
        return blocks

    # -- block readers ------------------------------------------------------
    def _code(self, i: int, fence: str, blocks: list[Block]) -> int:
        start = i
        body: list[str] = []
        i += 1
        closed = False
        while i < len(self.lines):
            line = self.lines[i]
            stripped = line.strip()
            if stripped.startswith(fence[0] * len(fence)) and set(stripped) == {fence[0]}:
                closed = True
                i += 1
                break
            body.append(line)
            i += 1
        if not closed:
            self.warnings.add(self.loc(start), "khối mã không có dấu đóng; lấy đến hết file")
        blocks.append(Block("code", self.loc(start), text="\n".join(body)))
        return i

    def _cover(self, i: int, blocks: list[Block]) -> int:
        start = i
        children: list[Block] = []
        i += 1
        while i < len(self.lines):
            line = self.lines[i]
            # The cover ends at the next heading of any level (e.g. "## Thông tin thực hiện").
            if HEADING_RE.match(line):
                break
            stripped = line.strip()
            if stripped.endswith("\\"):
                stripped = stripped[:-1].rstrip()
            if not stripped:
                children.append(Block("blank", self.loc(i)))
            else:
                figure = FIGURE_RE.match(stripped)
                if figure:
                    children.append(Block("image", self.loc(i), text=figure.group("path")))
                else:
                    children.append(Block("para", self.loc(i), segs=parse_inline(stripped)))
            i += 1
        while children and children[0].kind == "blank":
            children.pop(0)
        while children and children[-1].kind == "blank":
            children.pop()
        blocks.append(Block("cover", self.loc(start), children=children))
        return i

    def _refdef(self, i: int, match: re.Match[str], blocks: list[Block]) -> int:
        start = i
        parts = [match.group(2).strip()]
        i += 1
        while i < len(self.lines):
            line = self.lines[i]
            if not line.strip() or REFDEF_RE.match(line) or HEADING_RE.match(line):
                break
            parts.append(line.strip())
            i += 1
        text = " ".join(p for p in parts if p)
        blocks.append(
            Block("refdef", self.loc(start), text=match.group(1), segs=parse_inline(text))
        )
        return i

    def _table(self, i: int, blocks: list[Block]) -> int:
        start = i
        header_raw = _split_row(self.lines[i])
        aligns = [_align_of(s) for s in _split_row(self.lines[i + 1])]
        ncols = len(header_raw)
        aligns = (aligns + ["left"] * ncols)[:ncols]
        i += 2
        rows: list[list[list[Seg]]] = []
        while i < len(self.lines) and self.lines[i].strip() and "|" in self.lines[i]:
            cells = _split_row(self.lines[i])
            if len(cells) > ncols:
                self.warnings.add(
                    self.loc(i), f"hàng có {len(cells)} ô, bảng có {ncols} cột; bỏ ô thừa"
                )
                cells = cells[:ncols]
            cells += [""] * (ncols - len(cells))
            rows.append([parse_inline(c) for c in cells])
            i += 1
        blocks.append(
            Block(
                "table",
                self.loc(start),
                header=[parse_inline(c) for c in header_raw],
                rows=rows,
                aligns=aligns,
            )
        )
        return i

    def _list(self, i: int, blocks: list[Block]) -> int:
        start = i
        raw: list[tuple[int, bool, int, list[str]]] = []
        lines = self.lines
        while i < len(lines):
            line = lines[i]
            match = LIST_RE.match(line)
            if match:
                indent = len(match.group("indent").expandtabs(4))
                marker = match.group("marker")
                ordered = marker[0].isdigit()
                raw.append(
                    (
                        0 if indent < 2 else 1,
                        ordered,
                        int(marker[:-1]) if ordered else 0,
                        [match.group("text")],
                    )
                )
                i += 1
                continue
            if not line.strip():
                j = i
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and LIST_RE.match(lines[j]):
                    i = j
                    continue
                break
            if self._starts_block(i):
                break
            raw[-1][3].append(line.strip())
            i += 1
        items = [
            ListItem(level, ordered, number, parse_inline(" ".join(t.strip() for t in texts)))
            for level, ordered, number, texts in raw
        ]
        blocks.append(Block("list", self.loc(start), items=items))
        return i

    def _paragraph(self, i: int, blocks: list[Block]) -> int:
        start = i
        parts: list[str] = []
        while i < len(self.lines) and self.lines[i].strip():
            if i > start and self._starts_block(i):
                break
            parts.append(self.lines[i])
            i += 1
        pieces: list[str] = []
        for idx, part in enumerate(parts):
            hard_break = part.endswith("  ") or part.rstrip().endswith("\\")
            text = part.strip()
            if text.endswith("\\") and not text.endswith("\\\\"):
                text = text[:-1].rstrip()
            pieces.append(text)
            if idx < len(parts) - 1:
                pieces.append("\n" if hard_break else " ")
        blocks.append(Block("para", self.loc(start), segs=parse_inline("".join(pieces))))
        return i


def attach_captions(blocks: list[Block], warnings: Warnings) -> list[Block]:
    """Join ``Bảng:`` lines to the next table and mark ``Nguồn:`` lines after figures/tables."""
    out: list[Block] = []
    for block in blocks:
        if block.kind == "table" and out and out[-1].kind == "table_caption":
            caption = out.pop()
            block.caption = caption.segs
            block.label = caption.label
        elif block.kind == "source" and out and out[-1].kind in ("figure", "table"):
            block.attached_to = out[-1].kind
        out.append(block)
    for block in out:
        if block.kind == "table_caption":
            warnings.add(
                block.loc, "dòng 'Bảng:' không có bảng pipe ngay sau; dựng như đoạn thường"
            )
            block.kind = "para"
            block.segs = parse_inline(block.text)
    return out


def read_sections(sections_dir: Path, warnings: Warnings) -> list[Block]:
    """Parse every section file (sorted by name, README.md skipped) into one block list."""
    if not sections_dir.is_dir():
        raise ReportInputError(f"không có thư mục sections: {sections_dir}")
    files = sorted(
        (p for p in sections_dir.glob("*.md") if p.name.lower() != "readme.md"),
        key=lambda p: p.name,
    )
    if not files:
        raise ReportInputError(f"không có file .md nào trong {sections_dir}")
    blocks: list[Block] = []
    for path in files:
        # NFC so that regexes on Vietnamese words match whatever the editor saved.
        text = unicodedata.normalize("NFC", path.read_text(encoding="utf-8-sig"))
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = strip_html_comments(text, path.name, warnings)
        blocks.extend(MarkdownFileParser(path.name, text, warnings).parse())
    return attach_captions(blocks, warnings)


# ---------------------------------------------------------------------------
# Numbering pass (figures, tables, labels, citation order)
# ---------------------------------------------------------------------------


@dataclass
class Numbering:
    """Result of the first pass over the whole document."""

    labels: dict[str, str] = field(default_factory=dict)  # "fig:x" -> "Hình 2.1"
    cite_numbers: dict[str, int] = field(default_factory=dict)
    ref_defs: dict[str, Block] = field(default_factory=dict)
    chapters: int = 0
    other_level1: int = 0
    figures: int = 0
    tables: int = 0
    unnumbered_tables: int = 0
    citation_uses: int = 0


def chapter_key(title: str) -> str | None:
    """Return the chapter number/letter used in captions, or None for unnumbered parts."""
    match = CHAPTER_RE.match(title) or APPENDIX_RE.match(title)
    return match.group(1) if match else None


def segs_to_plain(segs: list[Seg], numbering: Numbering | None = None) -> str:
    """Flatten segments to text, resolving citations/cross-references when possible."""
    parts: list[str] = []
    for seg in segs:
        if seg.kind == "cite" and numbering is not None:
            parts.append(
                ", ".join(
                    f"[{numbering.cite_numbers[k]}]" if k in numbering.cite_numbers else f"[@{k}]"
                    for k in seg.keys
                )
            )
        elif seg.kind == "xref" and numbering is not None:
            parts.append(numbering.labels.get(seg.ref, seg.text))
        else:
            parts.append(seg.text)
    return "".join(parts).replace("\n", " ")


def iter_block_segs(blocks: list[Block]) -> Iterator[tuple[Block, list[Seg]]]:
    """Yield every inline segment list in reading order (reference definitions excluded)."""
    for block in blocks:
        if block.kind == "cover":
            for child in block.children:
                yield child, child.segs
        elif block.kind == "list":
            for item in block.items:
                yield block, item.segs
        elif block.kind == "table":
            if block.caption is not None:
                yield block, block.caption
            for row in [block.header, *block.rows]:
                for cell in row:
                    yield block, cell
        elif block.kind != "refdef":
            yield block, block.segs


def number_document(blocks: list[Block], warnings: Warnings) -> Numbering:
    """Assign figure/table numbers per chapter and citation numbers by first use."""
    numbering = Numbering()
    for block in blocks:
        if block.kind == "refdef":
            if block.text in numbering.ref_defs:
                warnings.add(
                    block.loc, f"khoá tài liệu [@{block.text}] bị khai báo lại; dùng bản đầu"
                )
            else:
                numbering.ref_defs[block.text] = block

    key: str | None = None
    fig_k = tbl_k = 0
    for block in blocks:
        if block.kind == "heading" and block.level == 1:
            key = chapter_key(segs_to_plain(block.segs))
            if CHAPTER_RE.match(segs_to_plain(block.segs)):
                numbering.chapters += 1
            else:
                numbering.other_level1 += 1
            fig_k = tbl_k = 0
        elif block.kind == "figure":
            fig_k += 1
            numbering.figures += 1
            block.number = f"{key}.{fig_k}" if key else str(fig_k)
            _register(numbering, block, FIGURE_WORD, "fig:", warnings)
        elif block.kind == "table":
            if block.caption is None:
                numbering.unnumbered_tables += 1
                continue
            tbl_k += 1
            numbering.tables += 1
            block.number = f"{key}.{tbl_k}" if key else str(tbl_k)
            _register(numbering, block, TABLE_WORD, "tbl:", warnings)

    for block, segs in iter_block_segs(blocks):
        for seg in segs:
            if seg.kind != "cite":
                continue
            numbering.citation_uses += 1
            for cite_key in seg.keys:
                if cite_key in numbering.ref_defs and cite_key not in numbering.cite_numbers:
                    numbering.cite_numbers[cite_key] = len(numbering.cite_numbers) + 1
    return numbering


def _register(
    numbering: Numbering, block: Block, word: str, prefix: str, warnings: Warnings
) -> None:
    if not block.label:
        return
    if not block.label.startswith(prefix):
        warnings.add(block.loc, f"nhãn {block.label} không bắt đầu bằng {prefix}")
    if block.label in numbering.labels:
        warnings.add(block.loc, f"nhãn {block.label} bị trùng; giữ số của lần đầu")
        return
    numbering.labels[block.label] = f"{word} {block.number}"


def detect_title(blocks: list[Block]) -> str:
    """Pick the report title from the cover: a 'Đề tài:' line, else the first text line."""
    cover = next((b for b in blocks if b.kind == "cover"), None)
    if cover is None:
        return ""
    texts = [segs_to_plain(c.segs).strip() for c in cover.children if c.kind == "para"]
    texts = [t for t in texts if t]
    for idx, text in enumerate(texts):
        match = re.match(r"^(?:tên\s+)?đề\s+tài\s*:?\s*(.*)$", text, re.IGNORECASE)
        if match:
            if match.group(1).strip():
                return match.group(1).strip()
            if idx + 1 < len(texts):
                return texts[idx + 1]
    return texts[0] if texts else ""


# ---------------------------------------------------------------------------
# Low-level OOXML helpers
# ---------------------------------------------------------------------------
PPR_ORDER = [
    "pStyle",
    "keepNext",
    "keepLines",
    "pageBreakBefore",
    "framePr",
    "widowControl",
    "numPr",
    "suppressLineNumbers",
    "pBdr",
    "shd",
    "tabs",
    "suppressAutoHyphens",
    "kinsoku",
    "wordWrap",
    "overflowPunct",
    "topLinePunct",
    "autoSpaceDE",
    "autoSpaceDN",
    "bidi",
    "adjustRightInd",
    "snapToGrid",
    "spacing",
    "ind",
    "contextualSpacing",
    "mirrorIndents",
    "suppressOverlap",
    "jc",
    "textDirection",
    "textAlignment",
    "textboxTightWrap",
    "outlineLvl",
    "divId",
    "cnfStyle",
    "rPr",
    "sectPr",
    "pPrChange",
]
SECTPR_AFTER_PGNUM = [
    "cols",
    "formProt",
    "vAlign",
    "noEndnote",
    "titlePg",
    "textDirection",
    "bidi",
    "rtlGutter",
    "docGrid",
    "printerSettings",
    "sectPrChange",
]
SETTINGS_AFTER_UPDATE_FIELDS = [
    "hdrShapeDefaults",
    "footnotePr",
    "endnotePr",
    "compat",
    "docVars",
    "rsids",
    "mathPr",
    "attachedSchema",
    "themeFontLang",
    "clrSchemeMapping",
    "doNotIncludeSubdocsInStats",
    "doNotAutoCompressPictures",
    "forceUpgrade",
    "captions",
    "readModeInkLockDown",
    "smartTagType",
    "schemaLibrary",
    "shapeDefaults",
    "doNotEmbedSmartTags",
    "decimalSymbol",
    "listSeparator",
]


def _insert_before(parent, element, successors: list[str]) -> None:
    """Insert ``element`` before the first existing child named in ``successors``."""
    names = {qn(f"w:{s}") for s in successors}
    for child in parent:
        if child.tag in names:
            child.addprevious(element)
            return
    parent.append(element)


def _ppr_insert(paragraph: Paragraph, element) -> None:
    name = element.tag.split("}")[1]
    ppr = paragraph._p.get_or_add_pPr()
    existing = ppr.find(qn(f"w:{name}"))
    if existing is not None:
        ppr.remove(existing)
    _insert_before(ppr, element, PPR_ORDER[PPR_ORDER.index(name) + 1 :])


def set_rfonts(rpr, name: str) -> None:
    """Set one font for ascii/hAnsi/eastAsia/cs so Vietnamese text renders consistently."""
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        rfonts.attrib.pop(qn(attr), None)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)


def _set_size_cs(rpr, size_pt: float) -> None:
    szcs = rpr.find(qn("w:szCs"))
    if szcs is None:
        szcs = OxmlElement("w:szCs")
        sz = rpr.find(qn("w:sz"))
        if sz is not None:
            sz.addnext(szcs)
        else:
            rpr.append(szcs)
    szcs.set(qn("w:val"), str(int(size_pt * 2)))


def _fld_char(paragraph: Paragraph, char_type: str, dirty: bool = False) -> None:
    run = OxmlElement("w:r")
    fld = OxmlElement("w:fldChar")
    fld.set(qn("w:fldCharType"), char_type)
    if dirty:
        fld.set(qn("w:dirty"), "true")
    run.append(fld)
    paragraph._p.append(run)


def _instr_text(paragraph: Paragraph, instr: str) -> None:
    run = OxmlElement("w:r")
    text = OxmlElement("w:instrText")
    text.set(qn("xml:space"), "preserve")
    text.text = f" {instr} "
    run.append(text)
    paragraph._p.append(run)


def _inline_field(paragraph: Paragraph, instr: str, result: str, bold: bool = False) -> None:
    """Append a one-paragraph complex field whose cached result is ``result``.

    A complex field (not w:fldSimple) keeps the result in an ordinary run, so readers
    that ignore fields (python-docx ``.text``, some converters) still see the number.
    """
    _fld_char(paragraph, "begin")
    _instr_text(paragraph, instr)
    _fld_char(paragraph, "separate")
    run = paragraph.add_run(result)
    if bold:
        run.bold = True
    _fld_char(paragraph, "end")


def _no_indent(paragraph: Paragraph, align=WD_ALIGN_PARAGRAPH.LEFT) -> None:
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(0)
    fmt.alignment = align


# ---------------------------------------------------------------------------
# Rendering pass
# ---------------------------------------------------------------------------


class DocxRenderer:
    """Turns the numbered block list into a python-docx Document."""

    def __init__(self, numbering: Numbering, root: Path, warnings: Warnings) -> None:
        self.numbering = numbering
        self.root = root
        self.warnings = warnings
        self.doc: DocxDocument = Document()
        self.missing_images = 0
        self.refs_done = False
        self.text_width_cm = PAGE_WIDTH_CM - MARGIN_LEFT_CM - MARGIN_RIGHT_CM
        self.text_height_cm = PAGE_HEIGHT_CM - MARGIN_TOP_CM - MARGIN_BOTTOM_CM

    # -- setup ---------------------------------------------------------------
    def setup(self, update_fields_on_open: bool) -> None:
        """Configure page size, margins, styles and document settings."""
        self._setup_section(self.doc.sections[0])
        self._setup_styles()
        if update_fields_on_open:
            settings = self.doc.settings.element
            if settings.find(qn("w:updateFields")) is None:
                element = OxmlElement("w:updateFields")
                element.set(qn("w:val"), "true")
                _insert_before(settings, element, SETTINGS_AFTER_UPDATE_FIELDS)

    def _setup_section(self, section) -> None:
        section.page_width = Cm(PAGE_WIDTH_CM)
        section.page_height = Cm(PAGE_HEIGHT_CM)
        section.left_margin = Cm(MARGIN_LEFT_CM)
        section.right_margin = Cm(MARGIN_RIGHT_CM)
        section.top_margin = Cm(MARGIN_TOP_CM)
        section.bottom_margin = Cm(MARGIN_BOTTOM_CM)
        section.footer_distance = Cm(1.0)
        section.header_distance = Cm(1.0)

    def _setup_styles(self) -> None:
        styles = self.doc.styles
        defaults = styles.element.find(qn("w:docDefaults"))
        if defaults is not None:
            rpr = defaults.find(f"{qn('w:rPrDefault')}/{qn('w:rPr')}")
            if rpr is not None:
                set_rfonts(rpr, FONT_NAME)

        normal = styles["Normal"]
        normal.font.name = FONT_NAME
        normal.font.size = Pt(BODY_SIZE_PT)
        rpr = normal.element.get_or_add_rPr()
        set_rfonts(rpr, FONT_NAME)
        _set_size_cs(rpr, BODY_SIZE_PT)
        lang = rpr.find(qn("w:lang"))
        if lang is None:
            lang = OxmlElement("w:lang")
            rpr.append(lang)
        lang.set(qn("w:val"), "vi-VN")
        fmt = normal.paragraph_format
        fmt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        fmt.first_line_indent = Cm(FIRST_LINE_INDENT_CM)
        fmt.line_spacing = LINE_SPACING
        fmt.space_before = Pt(0)
        fmt.space_after = Pt(PARAGRAPH_SPACE_AFTER_PT)

        for level, size in HEADING_SIZES_PT.items():
            style = styles[f"Heading {level}"]
            self._style_font(style, size, bold=True, italic=level == 4)
            hfmt = style.paragraph_format
            hfmt.alignment = WD_ALIGN_PARAGRAPH.LEFT
            hfmt.first_line_indent = Cm(0)
            hfmt.left_indent = Cm(0)
            hfmt.space_before = Pt(12 if level > 1 else 0)
            hfmt.space_after = Pt(6 if level > 1 else 12)
            hfmt.line_spacing = LINE_SPACING
            hfmt.keep_with_next = True
            hfmt.page_break_before = level == 1

        caption = self._get_or_add_style("Caption")
        self._style_font(caption, CAPTION_SIZE_PT, bold=False, italic=False)
        cfmt = caption.paragraph_format
        cfmt.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cfmt.first_line_indent = Cm(0)
        cfmt.space_before = Pt(6)
        cfmt.space_after = Pt(6)
        cfmt.line_spacing = 1.15

        front = self._get_or_add_style("Front Title")
        front.base_style = normal
        self._style_font(front, HEADING_SIZES_PT[1], bold=True, italic=False)
        ffmt = front.paragraph_format
        ffmt.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ffmt.first_line_indent = Cm(0)
        ffmt.space_after = Pt(12)

        for name in ("Footer", "Header"):
            style = self._get_or_add_style(name)
            set_rfonts(style.element.get_or_add_rPr(), FONT_NAME)

    def _get_or_add_style(self, name: str):
        try:
            return self.doc.styles[name]
        except KeyError:
            style = self.doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            style.base_style = self.doc.styles["Normal"]
            return style

    @staticmethod
    def _style_font(style, size: float, bold: bool, italic: bool) -> None:
        style.font.name = FONT_NAME
        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.italic = italic
        style.font.color.rgb = BLACK
        rpr = style.element.get_or_add_rPr()
        color = rpr.find(qn("w:color"))
        if color is not None:
            for attr in ("w:themeColor", "w:themeShade", "w:themeTint"):
                color.attrib.pop(qn(attr), None)
        set_rfonts(rpr, FONT_NAME)
        _set_size_cs(rpr, size)

    # -- inline rendering ------------------------------------------------------
    def _run(
        self,
        paragraph: Paragraph,
        text: str,
        *,
        bold: bool = False,
        italic: bool = False,
        size: float | None = None,
        highlight: bool = False,
        red: bool = False,
        font: str | None = None,
    ) -> None:
        lines = text.split("\n")
        for idx, line in enumerate(lines):
            run = paragraph.add_run(line)
            if idx < len(lines) - 1:
                run.add_break()
            if bold:
                run.bold = True
            if italic:
                run.italic = True
            if size is not None:
                run.font.size = Pt(size)
            if highlight:
                run.font.highlight_color = WD_COLOR_INDEX.YELLOW
            if red:
                run.font.color.rgb = RED
            if font:
                set_rfonts(run._r.get_or_add_rPr(), font)

    def add_segments(
        self,
        paragraph: Paragraph,
        segs: list[Seg],
        loc: str,
        *,
        bold: bool = False,
        italic: bool = False,
        size: float | None = None,
    ) -> None:
        """Append inline segments as runs, resolving citations and cross-references."""
        for seg in segs:
            style = {
                "bold": bold or seg.bold,
                "italic": italic or seg.italic,
                "size": size,
                "highlight": seg.highlight,
            }
            if seg.kind == "text":
                self._run(paragraph, seg.text, **style)
            elif seg.kind == "code":
                self._run(paragraph, seg.text, font=CODE_FONT_NAME, **style)
            elif seg.kind == "cite":
                for idx, key in enumerate(seg.keys):
                    if idx:
                        self._run(paragraph, ", ", **style)
                    number = self.numbering.cite_numbers.get(key)
                    if number is None:
                        self.warnings.add(
                            loc, f"trích dẫn [@{key}] không có trong danh sách tài liệu tham khảo"
                        )
                        self._run(paragraph, f"[@{key}]", red=True, **style)
                    else:
                        self._run(paragraph, f"[{number}]", **style)
            elif seg.kind == "xref":
                target = self.numbering.labels.get(seg.ref)
                if target is None:
                    self.warnings.add(
                        loc, f"tham chiếu {seg.text} không có hình/bảng nào mang nhãn này"
                    )
                    self._run(paragraph, seg.text, red=True, **style)
                else:
                    self._run(paragraph, target, **style)

    # -- document parts ----------------------------------------------------------
    def render(self, blocks: list[Block], title: str, author: str) -> None:
        """Render cover, front matter (TOC, lists) and all body blocks."""
        cover = next((b for b in blocks if b.kind == "cover"), None)
        if cover is not None:
            self._render_cover(cover)
            body_section = self.doc.add_section(WD_SECTION.NEW_PAGE)
        else:
            body_section = self.doc.sections[0]
        self._setup_page_numbers(body_section)
        body = [b for b in blocks if b.kind != "cover"]
        first_h1 = next(
            (i for i, b in enumerate(body) if b.kind == "heading" and b.level == 1), len(body)
        )
        # Blocks between the cover and the first chapter (team info, task table) get their own
        # page(s) right after the cover, before the table of contents.
        front, rest = body[:first_h1], body[first_h1:]
        if front:
            self._render_body(front, final=False)
        self._render_front_matter(blocks, new_page=bool(front))
        self._render_body(rest)
        props = self.doc.core_properties
        props.title = title
        props.author = author
        props.last_modified_by = author
        props.language = "vi-VN"
        now = datetime.now(UTC).replace(microsecond=0, tzinfo=None)
        props.created = now
        props.modified = now
        props.revision = 1

    def _render_cover(self, cover: Block) -> None:
        for child in cover.children:
            paragraph = self.doc.add_paragraph()
            _no_indent(paragraph, WD_ALIGN_PARAGRAPH.CENTER)
            paragraph.paragraph_format.space_after = Pt(0)
            if child.kind == "para":
                self.add_segments(paragraph, child.segs, child.loc)
            elif child.kind == "image":
                self._add_picture(paragraph, child.text, child.loc, COVER_IMAGE_MAX_HEIGHT_CM)

    def _setup_page_numbers(self, section) -> None:
        section.footer.is_linked_to_previous = False
        paragraph = section.footer.paragraphs[0]
        _no_indent(paragraph, WD_ALIGN_PARAGRAPH.CENTER)
        _inline_field(paragraph, "PAGE", "1")
        sect_pr = section._sectPr
        pg_num = sect_pr.find(qn("w:pgNumType"))
        if pg_num is None:
            pg_num = OxmlElement("w:pgNumType")
            _insert_before(sect_pr, pg_num, SECTPR_AFTER_PGNUM)
        pg_num.set(qn("w:start"), "1")

    def _render_front_matter(self, blocks: list[Block], new_page: bool) -> None:
        toc_title = self.doc.add_paragraph("MỤC LỤC", style="Front Title")
        toc_title.paragraph_format.page_break_before = new_page
        entries = [
            (b.level, segs_to_plain(b.segs, self.numbering))
            for b in blocks
            if b.kind == "heading" and b.level <= 3
        ]
        self._field_block('TOC \\o "1-3" \\h \\z \\u', TOC_HINT, entries)

        figures = [b for b in blocks if b.kind == "figure"]
        tables = [b for b in blocks if b.kind == "table" and b.caption is not None]
        first_list = True
        for word, title, items in (
            (FIGURE_WORD, "DANH MỤC HÌNH", figures),
            (TABLE_WORD, "DANH MỤC BẢNG", tables),
        ):
            if not items:
                continue
            heading = self.doc.add_paragraph(title, style="Front Title")
            if first_list:
                heading.paragraph_format.page_break_before = True
            else:
                heading.paragraph_format.space_before = Pt(18)
            first_list = False
            caption_entries = [
                (
                    1,
                    self._caption_plain(
                        word, b.number, b.segs if word == FIGURE_WORD else b.caption or []
                    ),
                )
                for b in items
            ]
            self._field_block(f'TOC \\h \\z \\c "{word}"', LIST_HINT, caption_entries)

    def _caption_plain(self, word: str, number: str, segs: list[Seg]) -> str:
        text = segs_to_plain(segs, self.numbering).strip()
        return f"{word} {number}. {text}" if text else f"{word} {number}."

    def _field_block(self, instr: str, hint: str, entries: list[tuple[int, str]]) -> None:
        """Add a (possibly multi-paragraph) Word field whose cached result is a static list."""
        first = self.doc.add_paragraph()
        _no_indent(first)
        _fld_char(first, "begin", dirty=True)
        _instr_text(first, instr)
        _fld_char(first, "separate")
        self._run(first, hint, italic=True)
        first.runs[-1].font.color.rgb = GREY
        last = first
        for level, text in entries:
            paragraph = self.doc.add_paragraph()
            _no_indent(paragraph)
            fmt = paragraph.paragraph_format
            fmt.left_indent = Cm(0.6 * (level - 1))
            fmt.space_after = Pt(2)
            self._run(paragraph, text, bold=level == 1 and instr.startswith("TOC \\o"))
            last = paragraph
        _fld_char(last, "end")

    def _render_body(self, blocks: list[Block], final: bool = True) -> None:
        for idx, block in enumerate(blocks):
            next_kind = blocks[idx + 1].kind if idx + 1 < len(blocks) else ""
            if block.kind == "heading":
                paragraph = self.doc.add_paragraph(style=f"Heading {block.level}")
                self.add_segments(paragraph, block.segs, block.loc)
            elif block.kind == "para":
                paragraph = self.doc.add_paragraph()
                self.add_segments(paragraph, block.segs, block.loc)
            elif block.kind == "list":
                self._render_list(block)
            elif block.kind == "code":
                self._render_code(block)
            elif block.kind == "figure":
                self._render_figure(block)
            elif block.kind == "table":
                self._render_table(block, add_spacer=next_kind not in ("source",))
            elif block.kind == "source":
                self._render_source(block)
            elif block.kind == "refdef" and not self.refs_done:
                # The whole numbered list is printed where the first definition stands.
                self._render_references(block.loc)
                self.refs_done = True
        if final and not self.refs_done and self.numbering.citation_uses:
            self.warnings.add(
                "",
                "có trích dẫn nhưng không có dòng '[@khoa]: ...' nào "
                "(thiếu danh sách tài liệu tham khảo)",
            )

    def _render_list(self, block: Block) -> None:
        counters: dict[int, int | None] = {0: None, 1: None}
        for item in block.items:
            if item.level == 0:
                counters[1] = None
            if item.ordered:
                current = counters[item.level]
                counters[item.level] = item.number if current is None else current + 1
                marker = f"{counters[item.level]}."
            else:
                counters[item.level] = None
                marker = "•" if item.level == 0 else "◦"
            paragraph = self.doc.add_paragraph()
            fmt = paragraph.paragraph_format
            left = LIST_INDENT_CM + LIST_LEVEL_STEP_CM * item.level
            fmt.left_indent = Cm(left)
            fmt.first_line_indent = Cm(-LIST_HANGING_CM)
            fmt.tab_stops.add_tab_stop(Cm(left))
            fmt.space_after = Pt(3)
            self._run(paragraph, f"{marker}\t")
            self.add_segments(paragraph, item.segs, block.loc)

    def _render_code(self, block: Block) -> None:
        paragraph = self.doc.add_paragraph()
        _no_indent(paragraph)
        fmt = paragraph.paragraph_format
        fmt.line_spacing = 1.0
        fmt.space_before = Pt(3)
        fmt.space_after = Pt(PARAGRAPH_SPACE_AFTER_PT)
        fmt.keep_together = block.text.count("\n") < 25
        shading = OxmlElement("w:shd")
        shading.set(qn("w:val"), "clear")
        shading.set(qn("w:color"), "auto")
        shading.set(qn("w:fill"), CODE_SHADING_HEX)
        _ppr_insert(paragraph, shading)
        border = OxmlElement("w:pBdr")
        for side in ("top", "left", "bottom", "right"):
            edge = OxmlElement(f"w:{side}")
            edge.set(qn("w:val"), "single")
            edge.set(qn("w:sz"), "4")
            edge.set(qn("w:space"), "4")
            edge.set(qn("w:color"), "BFBFBF")
            border.append(edge)
        _ppr_insert(paragraph, border)
        self._run(paragraph, block.text, size=CODE_SIZE_PT, font=CODE_FONT_NAME)

    def _add_picture(
        self, paragraph: Paragraph, path_text: str, loc: str, max_height_cm: float
    ) -> bool:
        path = Path(path_text)
        if not path.is_absolute():
            path = self.root / path
        if not path.is_file():
            self.warnings.add(loc, f"không tìm thấy ảnh {path_text}")
            self._missing_image(paragraph, path_text)
            return False
        try:
            image = DocxImage.from_file(str(path))
            width_cm = image.px_width / (image.horz_dpi or 72) * 2.54
            height_cm = image.px_height / (image.vert_dpi or 72) * 2.54
            # Fit inside the text block, never upscale.
            scale = min(1.0, IMAGE_MAX_WIDTH_CM / width_cm, max_height_cm / height_cm)
            paragraph.add_run().add_picture(
                str(path), width=Cm(width_cm * scale), height=Cm(height_cm * scale)
            )
        # python-docx raises varied error types for unsupported/corrupt images; any of them
        # must become a warning, not stop the build.
        except Exception as exc:  # noqa: BLE001
            self.warnings.add(loc, f"không đọc được ảnh {path_text} ({type(exc).__name__}: {exc})")
            self._missing_image(paragraph, path_text)
            return False
        return True

    def _missing_image(self, paragraph: Paragraph, path_text: str) -> None:
        self.missing_images += 1
        self._run(paragraph, f"[THIẾU HÌNH: {path_text}]", bold=True, red=True)

    def _render_figure(self, block: Block) -> None:
        paragraph = self.doc.add_paragraph()
        _no_indent(paragraph, WD_ALIGN_PARAGRAPH.CENTER)
        fmt = paragraph.paragraph_format
        fmt.keep_with_next = True
        fmt.line_spacing = 1.0
        fmt.space_before = Pt(6)
        fmt.space_after = Pt(0)
        self._add_picture(
            paragraph, block.text, block.loc, self.text_height_cm - IMAGE_CAPTION_RESERVE_CM
        )
        self._add_caption(FIGURE_WORD, block.number, block.segs, block.loc, keep_with_next=False)

    def _add_caption(
        self, word: str, number: str, segs: list[Seg], loc: str, keep_with_next: bool
    ) -> None:
        paragraph = self.doc.add_paragraph(style="Caption")
        paragraph.paragraph_format.keep_with_next = keep_with_next
        chapter, _, k = number.rpartition(".")
        self._run(paragraph, f"{word} {chapter}." if chapter else f"{word} ", bold=True)
        # SEQ with \r pins the number, so Word's "update fields" keeps our per-chapter numbering
        # while TOC \c can still collect the caption into the list of figures/tables.
        _inline_field(paragraph, f"SEQ {word} \\r {k} \\* ARABIC", k, bold=True)
        if segs:
            self._run(paragraph, ". ", bold=True)
            self.add_segments(paragraph, segs, loc)
        else:
            self._run(paragraph, ".", bold=True)

    def _render_table(self, block: Block, add_spacer: bool) -> None:
        if block.caption is not None:
            self._add_caption(
                TABLE_WORD, block.number, block.caption, block.loc, keep_with_next=True
            )
        ncols = len(block.header)
        all_rows = [block.header, *block.rows]
        table = self.doc.add_table(rows=len(all_rows), cols=ncols)
        table.style = self.doc.styles["Table Grid"]
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True
        tbl_pr = table._tbl.tblPr
        tbl_w = tbl_pr.find(qn("w:tblW"))
        if tbl_w is None:
            tbl_w = OxmlElement("w:tblW")
            tbl_pr.append(tbl_w)
        tbl_w.set(qn("w:type"), "pct")
        tbl_w.set(qn("w:w"), "5000")

        weights = []
        for col in range(ncols):
            longest = max(len(segs_to_plain(row[col], self.numbering)) for row in all_rows)
            weights.append(min(max(longest, 4), 40) + 2)
        total = sum(weights)
        widths = [Cm(self.text_width_cm * w / total) for w in weights]
        align_map = {
            "left": WD_ALIGN_PARAGRAPH.LEFT,
            "center": WD_ALIGN_PARAGRAPH.CENTER,
            "right": WD_ALIGN_PARAGRAPH.RIGHT,
        }
        for col_idx, column in enumerate(table.columns):
            column.width = widths[col_idx]
        for row_idx, (row, cells) in enumerate(zip(table.rows, all_rows)):
            if row_idx == 0:
                header = OxmlElement("w:tblHeader")
                header.set(qn("w:val"), "true")
                row._tr.get_or_add_trPr().append(header)
            for col_idx, segs in enumerate(cells):
                cell = row.cells[col_idx]
                cell.width = widths[col_idx]
                paragraph = cell.paragraphs[0]
                align = (
                    WD_ALIGN_PARAGRAPH.CENTER if row_idx == 0 else align_map[block.aligns[col_idx]]
                )
                _no_indent(paragraph, align)
                fmt = paragraph.paragraph_format
                fmt.line_spacing = 1.15
                fmt.space_after = Pt(0)
                fmt.space_before = Pt(0)
                self.add_segments(paragraph, segs, block.loc, bold=row_idx == 0, size=TABLE_SIZE_PT)
        if add_spacer:
            spacer = self.doc.add_paragraph()
            _no_indent(spacer)
            spacer.paragraph_format.space_after = Pt(0)
            spacer.paragraph_format.line_spacing = 1.0
            spacer.add_run().font.size = Pt(6)

    def _render_source(self, block: Block) -> None:
        paragraph = self.doc.add_paragraph()
        if block.attached_to:
            align = (
                WD_ALIGN_PARAGRAPH.CENTER
                if block.attached_to == "figure"
                else WD_ALIGN_PARAGRAPH.LEFT
            )
            _no_indent(paragraph, align)
            paragraph.paragraph_format.space_before = Pt(3)
            self.add_segments(paragraph, block.segs, block.loc, italic=True, size=SOURCE_SIZE_PT)
        else:
            self.add_segments(paragraph, block.segs, block.loc)

    def _render_references(self, loc: str) -> None:
        cited = sorted(self.numbering.cite_numbers.items(), key=lambda kv: kv[1])
        ordered = [(number, key) for key, number in cited]
        next_number = len(ordered) + 1
        for key, block in self.numbering.ref_defs.items():
            if key not in self.numbering.cite_numbers:
                self.warnings.add(
                    block.loc, f"tài liệu [@{key}] không được trích dẫn ở đâu; in cuối danh sách"
                )
                ordered.append((next_number, key))
                next_number += 1
        for number, key in ordered:
            block = self.numbering.ref_defs[key]
            paragraph = self.doc.add_paragraph()
            fmt = paragraph.paragraph_format
            fmt.left_indent = Cm(1.0)
            fmt.first_line_indent = Cm(-1.0)
            fmt.tab_stops.add_tab_stop(Cm(1.0))
            self._run(paragraph, f"[{number}]\t")
            self.add_segments(paragraph, block.segs, block.loc)


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def build_report(
    sections_dir: Path,
    output: Path,
    root: Path,
    title: str | None = None,
    author: str = DEFAULT_AUTHOR,
    update_fields_on_open: bool = True,
) -> BuildResult:
    """Parse ``sections_dir``, render and save ``output``; return the build summary.

    Raises ReportInputError when there is nothing to build and OSError when saving fails.
    """
    warnings = Warnings()
    blocks = read_sections(sections_dir, warnings)
    numbering = number_document(blocks, warnings)
    final_title = title if title is not None else detect_title(blocks)
    if not final_title:
        warnings.add("", "không xác định được tên đề tài (không có '# BÌA'); dùng --title")
    renderer = DocxRenderer(numbering, root, warnings)
    renderer.setup(update_fields_on_open)
    renderer.render(blocks, final_title, author)
    output.parent.mkdir(parents=True, exist_ok=True)
    renderer.doc.save(str(output))
    return BuildResult(
        output=output,
        title=final_title,
        chapters=numbering.chapters,
        other_level1=numbering.other_level1,
        figures=numbering.figures,
        missing_images=renderer.missing_images,
        tables=numbering.tables,
        unnumbered_tables=numbering.unnumbered_tables,
        citation_uses=numbering.citation_uses,
        cited_sources=len(numbering.cite_numbers),
        references=len(numbering.ref_defs),
        warnings=warnings.items,
    )


def format_summary(result: BuildResult) -> str:
    """Return the human-readable summary printed at the end of a build."""
    lines = [
        f"Đã ghi: {result.output}",
        f"Tên đề tài: {result.title or '(trống)'}",
        f"Chương: {result.chapters} | Mục cấp 1 khác: {result.other_level1}",
        f"Hình: {result.figures} (thiếu/không đọc được ảnh: {result.missing_images})",
        f"Bảng có số: {result.tables} | Bảng không số: {result.unnumbered_tables}",
        (
            f"Trích dẫn: {result.citation_uses} lượt, {result.cited_sources} nguồn được trích, "
            f"{result.references} nguồn trong danh sách"
        ),
        f"Cảnh báo: {len(result.warnings)}",
    ]
    lines.extend(f"  - {w}" for w in result.warnings)
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line options; defaults are relative to the repository root."""
    parser = argparse.ArgumentParser(
        description="Build report/bao-cao.docx from report/sections/*.md"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT_DEFAULT,
        help="repository root; image paths are relative to it (default: auto)",
    )
    parser.add_argument(
        "--sections",
        type=Path,
        default=None,
        help="sections directory (default: <root>/report/sections)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="output .docx (default: <root>/report/bao-cao.docx)",
    )
    parser.add_argument(
        "--title", default=None, help="document title (default: taken from the cover)"
    )
    parser.add_argument("--author", default=DEFAULT_AUTHOR, help="document author property")
    parser.add_argument(
        "--no-update-on-open",
        action="store_true",
        help="do not ask Word to update fields (TOC, lists) when opening",
    )
    parser.add_argument(
        "--strict", action="store_true", help="exit with code 1 if there are warnings"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; returns the process exit code."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    root = args.root.resolve()
    sections = args.sections or root / "report" / "sections"
    output = args.output or root / "report" / "bao-cao.docx"
    try:
        result = build_report(
            sections, output, root, args.title, args.author, not args.no_update_on_open
        )
    except ReportInputError as exc:
        print(f"LỖI: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    except OSError as exc:
        print(f"LỖI: không ghi được {output} (file đang mở trong Word?): {exc}", file=sys.stderr)
        return EXIT_OUTPUT_ERROR
    print(format_summary(result))
    if args.strict and result.warnings:
        return EXIT_STRICT_WARNINGS
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
