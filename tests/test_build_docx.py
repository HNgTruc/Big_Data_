"""Tests for report/build/build_docx.py on a tiny Markdown fixture built in tmp_path."""

from __future__ import annotations

import importlib.util
import struct
import sys
import zlib
from pathlib import Path

import pytest

docx = pytest.importorskip("docx")
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml.ns import qn

SCRIPT = Path(__file__).resolve().parents[1] / "report" / "build" / "build_docx.py"
_spec = importlib.util.spec_from_file_location("build_docx", SCRIPT)
build_docx = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
# dataclasses look the module up in sys.modules while the class body executes.
sys.modules["build_docx"] = build_docx
_spec.loader.exec_module(build_docx)


def write_png(path: Path, width: int = 40, height: int = 20) -> None:
    """Write a minimal valid RGB PNG without needing Pillow."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return (
            struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    raw = b"".join(b"\x00" + b"\x80\x40\x20" * width for _ in range(height))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


COVER = """# BÌA

TRƯỜNG ĐẠI HỌC SÀI GÒN

**ĐỀ TÀI: Đánh giá hiệu năng thử nghiệm**

Sinh viên: [CHƯA CÓ: tên thành viên]

## Thông tin thực hiện

Bảng: Phân công {#tbl:phan-cong}

| Thành viên | Đóng góp |
|---|---|
| A | 100% |
"""

CHAPTER_1 = """# Chương 1. Giới thiệu

<!-- SECRET_COMMENT một dòng -->
Đoạn mở đầu trích [@beta] rồi xem @fig:later và @tbl:metrics, nhãn sai @fig:nope.

<!--
SECRET_MULTILINE
nhiều dòng
-->

Thiếu số liệu [CHƯA CÓ: số đo thật] ở đây; dùng `spark-submit` với **đậm** và *nghiêng*.

![Kiến trúc tổng quát](figs/ok.png){#fig:arch}

Nguồn: tác giả tự vẽ.

- mục một
  - mục con
- mục hai

1. bước một
2. bước hai

```
docker compose up -d
```
"""

CHAPTER_2 = """# Chương 2. Thực nghiệm

Trích nhiều nguồn [@alpha; @beta] và khoá lạ [@ghost].

![Hình không tồn tại](figs/missing.png){#fig:missing}

![Hình phía sau](figs/ok.png){#fig:later}

Bảng: Số đo thời gian {#tbl:metrics}

| Kích thước | Thời gian (s) |
|---|---:|
| 1M | `12.5` |
| 5M | 40.1 |

Nguồn: results/fake.csv

| a | b |
|---|---|
| x | y |
"""

REFS = """# Tài liệu tham khảo

[@alpha]: A. Author, *Alpha book*, 2020.
[@beta]: B. Author, "Beta paper," 2021.
[@unused]: C. Author, "Never cited," 2022.
"""


@pytest.fixture()
def built(tmp_path: Path):
    """Build the fixture report and return (result, Document)."""
    sections = tmp_path / "report" / "sections"
    sections.mkdir(parents=True)
    (sections / "00-bia.md").write_text(COVER, encoding="utf-8")
    (sections / "01-gioi-thieu.md").write_text(CHAPTER_1, encoding="utf-8")
    (sections / "02-thuc-nghiem.md").write_text(CHAPTER_2, encoding="utf-8")
    (sections / "90-tai-lieu-tham-khao.md").write_text(REFS, encoding="utf-8")
    (sections / "README.md").write_text("# README_SHOULD_BE_SKIPPED\n", encoding="utf-8")
    write_png(tmp_path / "figs" / "ok.png")
    output = tmp_path / "report" / "bao-cao.docx"
    result = build_docx.build_report(sections, output, tmp_path)
    return result, docx.Document(str(output))


def texts(document) -> list[str]:
    return [p.text for p in document.paragraphs]


def body_text(document) -> str:
    return "\n".join(texts(document))


def test_figures_and_tables_numbered_per_chapter(built):
    result, document = built
    captions = [p.text for p in document.paragraphs if p.style.name == "Caption"]
    assert captions == [
        "Bảng 1. Phân công",
        "Hình 1.1. Kiến trúc tổng quát",
        "Hình 2.1. Hình không tồn tại",
        "Hình 2.2. Hình phía sau",
        "Bảng 2.1. Số đo thời gian",
    ]
    assert result.figures == 3 and result.tables == 2 and result.unnumbered_tables == 1
    assert len(document.tables) == 3


def test_forward_cross_reference_and_unknown_label(built):
    result, document = built
    intro = next(t for t in texts(document) if t.startswith("Đoạn mở đầu"))
    assert "xem Hình 2.2 và Bảng 2.1" in intro
    assert "@fig:nope" in intro
    para = next(p for p in document.paragraphs if p.text.startswith("Đoạn mở đầu"))
    bad = [r for r in para.runs if r.text == "@fig:nope"]
    assert bad and bad[0].font.color.rgb == build_docx.RED
    assert any("@fig:nope" in w for w in result.warnings)


def test_citations_numbered_by_first_appearance(built):
    result, document = built
    all_text = body_text(document)
    assert "trích [1] rồi" in all_text  # beta cited first
    assert "[2], [1]" in all_text  # [@alpha; @beta]
    assert "[@ghost]" in all_text
    refs = [t for t in texts(document) if t.startswith("[") and "\t" in t]
    assert refs[0].startswith("[1]\tB. Author")
    assert refs[1].startswith("[2]\tA. Author")
    assert refs[2].startswith("[3]\tC. Author")  # uncited goes last
    assert any("[@unused]" in w for w in result.warnings)
    assert any("[@ghost]" in w for w in result.warnings)
    assert result.cited_sources == 2 and result.references == 3


def test_html_comments_and_readme_are_dropped(built):
    _, document = built
    all_text = body_text(document)
    assert "SECRET_COMMENT" not in all_text
    assert "SECRET_MULTILINE" not in all_text
    assert "README_SHOULD_BE_SKIPPED" not in all_text


def test_missing_marker_is_highlighted(built):
    _, document = built
    runs = [
        r
        for p in document.paragraphs
        for r in p.runs
        if "CHƯA CÓ" in r.text or "số đo thật" in r.text
    ]
    assert runs
    assert all(r.font.highlight_color == WD_COLOR_INDEX.YELLOW for r in runs)


def test_missing_image_does_not_stop_build(built):
    result, document = built
    assert result.missing_images == 1
    assert "[THIẾU HÌNH: figs/missing.png]" in body_text(document)
    assert any("figs/missing.png" in w for w in result.warnings)
    assert len(document.inline_shapes) == 2  # the two figures pointing to ok.png
    width_cm = document.inline_shapes[0].width.cm
    assert 0 < width_cm <= build_docx.IMAGE_MAX_WIDTH_CM


def test_cover_is_separate_and_not_a_chapter(built):
    result, document = built
    assert result.chapters == 2 and result.other_level1 == 1
    assert result.title == "Đánh giá hiệu năng thử nghiệm"
    headings1 = [p.text for p in document.paragraphs if p.style.name == "Heading 1"]
    assert headings1 == ["Chương 1. Giới thiệu", "Chương 2. Thực nghiệm", "Tài liệu tham khảo"]
    assert document.paragraphs[0].text == "TRƯỜNG ĐẠI HỌC SÀI GÒN"
    assert len(document.sections) == 2
    # Team info follows the cover on its own page, before the table of contents.
    order = texts(document)
    info = order.index("Thông tin thực hiện")
    assert order.index("Sinh viên: [CHƯA CÓ: tên thành viên]") < info
    assert info < order.index("MỤC LỤC")
    info_para = next(p for p in document.paragraphs if p.text == "Thông tin thực hiện")
    assert info_para.style.name == "Heading 2"
    assert document.tables[0].rows[1].cells[1].text == "100%"
    cover_footer = document.sections[0]._sectPr.findall(qn("w:footerReference"))
    assert cover_footer == []
    footer_xml = document.sections[1].footer._element.xml
    assert "PAGE" in footer_xml
    assert document.sections[1]._sectPr.find(qn("w:pgNumType")).get(qn("w:start")) == "1"
    assert document.core_properties.title == result.title
    assert document.core_properties.author == build_docx.DEFAULT_AUTHOR
    assert document.core_properties.author.count(";") == 3  # all four team members


def test_abstract_and_appendices_keep_their_own_numbering(tmp_path: Path):
    sections = tmp_path / "report" / "sections"
    sections.mkdir(parents=True)
    files = {
        "00-bia.md": COVER,
        "00-tom-tat.md": "# Tóm tắt\n\nNội dung tóm tắt [@alpha].\n",
        "01-gioi-thieu.md": "# Chương 1. Giới thiệu\n\nXem @tbl:luoc-do, @fig:minh-chung và @tbl:cau-hinh.\n",
        "90-tai-lieu-tham-khao.md": "# Tài liệu tham khảo\n\n[@alpha]: A. Author, *Alpha book*, 2020.\n",
        "95-phu-luc-a-du-lieu.md": (
            "# Phụ lục A. Dữ liệu\n\nBảng: Lược đồ {#tbl:luoc-do}\n\n| a | b |\n|---|---|\n| x | y |\n\n"
            "![Minh chứng](figs/ok.png){#fig:minh-chung}\n\nNguồn: results/fake.csv\n"
        ),
        "95-phu-luc-b-cai-dat.md": (
            "# Phụ lục B. Cài đặt\n\nBảng: Cấu hình {#tbl:cau-hinh}\n\n| a | b |\n|---|---|\n| x | y |\n"
        ),
    }
    for name, content in files.items():
        (sections / name).write_text(content, encoding="utf-8")
    write_png(tmp_path / "figs" / "ok.png")
    output = tmp_path / "report" / "bao-cao.docx"

    result = build_docx.build_report(sections, output, tmp_path)
    document = docx.Document(str(output))

    assert result.warnings == []
    captions = [p.text for p in document.paragraphs if p.style.name == "Caption"]
    assert captions == ["Bảng 1. Phân công", "Bảng A.1. Lược đồ", "Hình A.1. Minh chứng", "Bảng B.1. Cấu hình"]
    assert "Xem Bảng A.1, Hình A.1 và Bảng B.1." in texts(document)
    # Appendices are level-1 parts, not chapters, and each one starts on a new page.
    assert result.chapters == 1 and result.other_level1 == 4
    assert document.styles["Heading 1"].paragraph_format.page_break_before is True
    headings1 = [p.text for p in document.paragraphs if p.style.name == "Heading 1"]
    assert headings1 == [
        "Tóm tắt",
        "Chương 1. Giới thiệu",
        "Tài liệu tham khảo",
        "Phụ lục A. Dữ liệu",
        "Phụ lục B. Cài đặt",
    ]
    # The abstract sits after the table of contents and is listed in it; its citation counts as first use.
    order = texts(document)
    abstract = next(i for i, p in enumerate(document.paragraphs) if p.style.name == "Heading 1")
    assert order.index("MỤC LỤC") < abstract
    assert "Nội dung tóm tắt [1]." in order


def test_toc_and_caption_fields(built):
    _, document = built
    xml = document.element.xml
    assert 'TOC \\o "1-3" \\h \\z \\u' in xml
    assert 'TOC \\h \\z \\c "Hình"' in xml
    assert 'TOC \\h \\z \\c "Bảng"' in xml
    assert "SEQ Hình \\r 2" in xml
    assert build_docx.TOC_HINT in body_text(document)


def test_table_formatting(built):
    _, document = built
    table = document.tables[1]
    assert [c.text for c in table.rows[0].cells] == ["Kích thước", "Thời gian (s)"]
    header_run = table.rows[0].cells[0].paragraphs[0].runs[0]
    assert header_run.bold and header_run.font.size.pt == build_docx.TABLE_SIZE_PT
    code_run = table.rows[1].cells[1].paragraphs[0].runs[0]
    assert code_run._r.rPr.rFonts.get(qn("w:ascii")) == "Consolas"
    source = next(p for p in document.paragraphs if p.text.startswith("Nguồn: results/fake.csv"))
    assert source.runs[0].italic and source.runs[0].font.size.pt == build_docx.SOURCE_SIZE_PT


def test_lists_code_and_heading_style(built):
    _, document = built
    all_text = texts(document)
    assert "•\tmục một" in all_text and "◦\tmục con" in all_text
    assert "1.\tbước một" in all_text and "2.\tbước hai" in all_text
    code = next(p for p in document.paragraphs if p.text == "docker compose up -d")
    assert code.runs[0].font.size.pt == build_docx.CODE_SIZE_PT
    heading = document.styles["Heading 1"]
    assert heading.font.size.pt == 16 and heading.font.bold
    assert heading.paragraph_format.page_break_before


def test_inline_parser_details():
    segs = build_docx.parse_inline(r"a **b `c*d`** \*e\* [@x; @y] @tbl:t1.")
    kinds = [(s.kind, s.text) for s in segs]
    assert ("code", "c*d") in kinds
    assert any(s.kind == "text" and s.text == "b " and s.bold for s in segs)
    assert any(s.kind == "text" and "*e*" in s.text for s in segs)
    cite = next(s for s in segs if s.kind == "cite")
    assert cite.keys == ("x", "y")
    xref = next(s for s in segs if s.kind == "xref")
    assert xref.ref == "tbl:t1"


def test_main_exit_codes(tmp_path: Path, capsys):
    assert build_docx.main(["--root", str(tmp_path)]) == build_docx.EXIT_INPUT_ERROR
    sections = tmp_path / "report" / "sections"
    sections.mkdir(parents=True)
    (sections / "01-a.md").write_text("# Chương 1. A\n\nXem @fig:none.\n", encoding="utf-8")
    assert build_docx.main(["--root", str(tmp_path)]) == build_docx.EXIT_OK
    assert (tmp_path / "report" / "bao-cao.docx").is_file()
    assert build_docx.main(["--root", str(tmp_path), "--strict"]) == build_docx.EXIT_STRICT_WARNINGS
    out = capsys.readouterr().out
    assert "Cảnh báo:" in out and "@fig:none" in out
