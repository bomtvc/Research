"""Stage 4 — EVIDENCE MATRIX: mỗi dòng là một số liệu truy được về nguồn."""
from __future__ import annotations

from typing import Any

from ..base import Ctx, Stage, RESEARCHER_SYSTEM, dump, topic_brief
from ..schemas import EVIDENCE_MATRIX

RESEARCH_PROMPT = """{brief}

# NGUỒN ĐÃ ĐƯỢC CHẤP NHẬN
{accepted}

# CÁC CHỈ SỐ CẦN THU THẬP
{indicators}

# NHIỆM VỤ
Dựng ma trận bằng chứng: bóc từng số liệu cụ thể ra khỏi các nguồn đã được chấp nhận.

Quy tắc:
- Một dòng = một số liệu = một khẳng định kiểm chứng được. Không gộp nhiều số liệu vào một dòng.
- Bắt buộc có: giá trị, đơn vị, năm, địa điểm (quận/trạm quan trắc/lưu vực nếu nguồn có nêu),
  và id nguồn.
- Dùng web_fetch mở lại nguồn khi cần lấy con số chính xác. Không nhớ áng chừng.
- Nếu hai nguồn cho hai con số khác nhau cho cùng một chỉ số và cùng năm, tạo hai dòng
  và ghi mâu thuẫn đó vào `conflicts`.
- Phủ đủ cả bốn nhóm: hiện trạng không khí, hiện trạng nước, nguyên nhân, hậu quả và giải pháp.
- `gaps`: chỉ số nào trong kế hoạch vẫn chưa có số liệu nào."""

EXTRACT_PROMPT = """Chuyển kết quả bóc tách thành ma trận bằng chứng JSON.

Quy tắc:
- id dòng dạng E01, E02, ...
- `source_ids` chỉ được dùng id nguồn đã được chấp nhận ở bước thẩm định.
- Dòng nào không truy được về nguồn nào thì loại bỏ, đừng giữ lại.
- `confidence` thấp nếu số liệu là ước tính, là số liệu cũ, hoặc chỉ có một nguồn thứ cấp."""


def run(ctx: Ctx) -> dict[str, Any]:
    plan = ctx.artifact("research_plan")
    discovery = ctx.artifact("source_discovery")
    verify = ctx.artifact("source_verify")

    accepted_ids = set(verify.get("accepted_ids", []))
    accepted = [s for s in discovery.get("sources", []) if s.get("id") in accepted_ids]
    ctx.log("  · bóc số liệu từ " + str(len(accepted)) + " nguồn")

    data, report, _ = ctx.client.research_json(
        system=RESEARCHER_SYSTEM,
        research_prompt=RESEARCH_PROMPT.format(
            brief=topic_brief(ctx.topic),
            accepted=dump(accepted),
            indicators=dump(plan.get("key_indicators", [])),
        ),
        extract_prompt=EXTRACT_PROMPT,
        schema=EVIDENCE_MATRIX,
        effort=ctx.effort("evidence_matrix"),
        max_searches=8,
        max_fetches=ctx.topic.get("max_fetches", 12),
    )

    ctx.state.write_text("04_evidence_report.md", report, folder="raw")
    rows = data.get("rows", [])
    ctx.log("  · ma trận có " + str(len(rows)) + " dòng bằng chứng, "
            + str(len(data.get("conflicts", []))) + " mâu thuẫn")
    return data


STAGE = Stage(
    num=4,
    key="evidence_matrix",
    title="Evidence Matrix",
    run=run,
    description="Số liệu ↔ nguồn, kèm mâu thuẫn và khoảng trống",
)
