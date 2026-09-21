"""Stage 8 — WRITING: viết từng mục theo dàn ý, có bằng chứng kèm sẵn."""
from __future__ import annotations

from typing import Any

from ..base import Ctx, Stage, WRITER_SYSTEM, dump, topic_brief

SECTION_PROMPT = """{brief}

# LUẬN ĐỀ TOÀN BÀI
{thesis}

# MỤC CẦN VIẾT
Tiêu đề: {heading}
Cấp tiêu đề: {level}
Mục đích trong mạch lập luận: {purpose}
Ý chính cần có:
{key_points}
Độ dài mục tiêu: khoảng {target_words} từ.

# LUẬN ĐIỂM ĐƯỢC PHÂN CÔNG CHO MỤC NÀY
{arguments}

# BẰNG CHỨNG ĐƯỢC PHÉP DÙNG TRONG MỤC NÀY
{evidence}

# DANH MỤC NGUỒN (dùng để trích dẫn)
{sources}

# ĐOẠN TRƯỚC ĐÓ (để nối mạch, không viết lại)
{previous}

# YÊU CẦU
- Viết bằng {language}, văn phong học thuật.
- Bắt đầu bằng đúng một dòng tiêu đề Markdown cấp {level} cho mục này, rồi viết nội dung.
- Mọi số liệu phải lấy từ khối bằng chứng ở trên và phải có trích dẫn dạng ({citation_hint}).
  Không có số liệu nào khác được phép xuất hiện.
- Nếu bằng chứng không đủ cho một ý trong dàn ý, viết rõ là dữ liệu hiện chưa cho phép kết luận,
  thay vì viết chung chung cho đủ chữ.
- Không viết phần kết luận của toàn bài ở đây trừ khi đây chính là mục kết luận.
- Chỉ trả về nội dung Markdown của mục, không thêm lời dẫn nào khác."""


def _index(items: list[dict[str, Any]], key: str = "id") -> dict[str, dict[str, Any]]:
    return {item[key]: item for item in items if item.get(key)}


def run(ctx: Ctx) -> dict[str, Any]:
    outline = ctx.artifact("outline")
    argmap = ctx.artifact("argument_map")
    matrix = ctx.artifact("evidence_matrix")
    discovery = ctx.artifact("source_discovery")
    verify = ctx.artifact("source_verify")

    rows = _index(matrix.get("rows", []))
    args = _index(argmap.get("arguments", []))
    solutions = _index(argmap.get("solution_arguments", []))
    accepted_ids = set(verify.get("accepted_ids", []))
    sources = [s for s in discovery.get("sources", []) if s.get("id") in accepted_ids]
    source_ref = [
        {"id": s["id"], "publisher": s.get("publisher", ""), "year": s.get("year", ""),
         "title": s.get("title", "")}
        for s in sources
    ]

    language = ctx.topic.get("language", "tiếng Việt")
    citation_hint = ctx.topic.get("citation_hint", "Tên cơ quan/tác giả, Năm")
    brief = topic_brief(ctx.topic)
    effort = ctx.effort("writing")

    parts: list[str] = []
    written: list[dict[str, Any]] = []
    previous = "(đây là mục đầu tiên)"

    sections = outline.get("sections", [])
    for i, section in enumerate(sections, start=1):
        heading = section.get("heading", "Mục " + str(i))
        ctx.log("  · [" + str(i) + "/" + str(len(sections)) + "] " + heading)

        picked_args = [args[a] for a in section.get("argument_ids", []) if a in args]
        picked_args += [solutions[a] for a in section.get("argument_ids", []) if a in solutions]
        picked_rows = [rows[r] for r in section.get("evidence_row_ids", []) if r in rows]

        text = ctx.client.text(
            system=WRITER_SYSTEM,
            prompt=SECTION_PROMPT.format(
                brief=brief,
                thesis=argmap.get("thesis", ""),
                heading=heading,
                level=section.get("level", 2),
                purpose=section.get("purpose", ""),
                key_points="\n".join("- " + p for p in section.get("key_points", [])),
                target_words=section.get("target_words", 400),
                arguments=dump(picked_args) if picked_args else "(mục này không gắn luận điểm nào)",
                evidence=dump(picked_rows) if picked_rows
                else "(mục này không có bằng chứng số liệu — viết phần dẫn dắt/khung khổ)",
                sources=dump(source_ref),
                previous=previous,
                language=language,
                citation_hint=citation_hint,
            ),
            effort=effort,
            max_tokens=16_000,
        )

        parts.append(text)
        written.append({
            "id": section.get("id", str(i)),
            "heading": heading,
            "words": len(text.split()),
        })
        previous = text[-1500:]

    draft = "\n\n".join(parts)
    path = ctx.state.write_text("draft.md", draft)
    total_words = sum(s["words"] for s in written)
    ctx.log("  · bản thảo " + str(total_words) + " từ -> " + str(path))

    return {
        "draft_file": "paper/draft.md",
        "word_count": total_words,
        "sections": written,
    }


STAGE = Stage(
    num=8,
    key="writing",
    title="Writing",
    run=run,
    description="Viết từng mục, mỗi mục chỉ được dùng bằng chứng của mục đó",
)
