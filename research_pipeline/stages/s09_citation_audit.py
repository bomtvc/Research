"""Stage 9 — CITATION AUDIT: soi trích dẫn, dựng danh mục tài liệu tham khảo."""
from __future__ import annotations

from typing import Any

from ..base import Ctx, Stage, REVIEWER_SYSTEM, dump, topic_brief
from ..schemas import CITATION_AUDIT

PROMPT = """{brief}

# BẢN THẢO
{draft}

# MA TRẬN BẰNG CHỨNG
{matrix}

# DANH MỤC NGUỒN ĐƯỢC CHẤP NHẬN
{sources}

# NHIỆM VỤ
Kiểm toán trích dẫn của bản thảo trên. Đây là bước máy móc, không phải bước góp ý văn phong.

Với từng câu có chứa số liệu hoặc khẳng định thực tế:
1. Câu đó có trích dẫn không? Không có → lỗi "thiếu trích dẫn".
2. Trích dẫn có trỏ tới nguồn thật trong danh mục không? Không → lỗi "nguồn không tồn tại trong danh mục".
3. Con số trong câu có khớp với dòng bằng chứng tương ứng không (giá trị, đơn vị, năm, địa điểm)?
   Lệch → lỗi "số liệu không khớp nguồn". Đây là lỗi nghiêm trọng.
4. Định dạng trích dẫn có nhất quán theo kiểu {citation_style} không?

Ngoài ra:
- `unused_sources`: nguồn đã thẩm định nhưng không được dùng câu nào.
- `bibliography`: danh mục tài liệu tham khảo hoàn chỉnh, sắp xếp theo bảng chữ cái,
  định dạng theo {citation_style}, chỉ gồm nguồn thực sự được trích trong bài.
- `verdict`: "không đạt" nếu còn bất kỳ lỗi nghiêm trọng nào.

Trích nguyên văn đoạn có lỗi vào `quoted_text` để bước sau sửa đúng chỗ."""


def run(ctx: Ctx) -> dict[str, Any]:
    draft = ctx.state.read_text("draft.md")
    matrix = ctx.artifact("evidence_matrix")
    discovery = ctx.artifact("source_discovery")
    verify = ctx.artifact("source_verify")
    accepted_ids = set(verify.get("accepted_ids", []))
    sources = [s for s in discovery.get("sources", []) if s.get("id") in accepted_ids]

    ctx.log("  · kiểm toán trích dẫn trên bản thảo " + str(len(draft.split())) + " từ")
    data = ctx.client.json(
        system=REVIEWER_SYSTEM,
        prompt=PROMPT.format(
            brief=topic_brief(ctx.topic),
            draft=draft,
            matrix=dump(matrix.get("rows", []), limit=60_000),
            sources=dump(sources),
            citation_style=ctx.topic.get("citation_style", "APA rút gọn"),
        ),
        schema=CITATION_AUDIT,
        effort=ctx.effort("citation_audit"),
    )

    issues = data.get("issues", [])
    severe = [i for i in issues if i.get("severity") == "nghiêm trọng"]
    ctx.log("  · " + str(len(issues)) + " lỗi trích dẫn (" + str(len(severe)) + " nghiêm trọng)"
            + " — kết luận: " + str(data.get("verdict")))
    return data


STAGE = Stage(
    num=9,
    key="citation_audit",
    title="Citation Audit",
    run=run,
    description="Câu nào thiếu trích dẫn, số nào lệch nguồn, tài liệu tham khảo",
)
