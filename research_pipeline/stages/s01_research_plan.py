"""Stage 1 — RESEARCH PLAN: biến đề tài thành kế hoạch nghiên cứu kiểm chứng được."""
from __future__ import annotations

from typing import Any

from ..base import Ctx, Stage, RESEARCHER_SYSTEM, topic_brief
from ..schemas import RESEARCH_PLAN

PROMPT = """{brief}

# NHIỆM VỤ
Lập kế hoạch nghiên cứu cho đề tài trên, trước khi tìm bất kỳ nguồn nào.

Yêu cầu cụ thể:
1. Phát biểu lại đề tài bằng ngôn ngữ nghiên cứu (rõ biến số, rõ phạm vi).
2. Đặt 6–9 câu hỏi nghiên cứu. Mỗi câu phải trả lời được bằng dữ liệu, không phải bằng ý kiến.
   Bao phủ cả bốn nhóm: (a) hiện trạng, (b) nguyên nhân, (c) hậu quả, (d) giải pháp và hiệu quả
   của giải pháp đã triển khai.
3. Chia đề tài thành các chủ đề con cho cả hai mảng ô nhiễm không khí và ô nhiễm nước.
4. Liệt kê các chỉ số đo lường cần thu thập (ví dụ: nồng độ bụi mịn, chỉ số chất lượng không khí,
   các chỉ tiêu chất lượng nước mặt, tỷ lệ nước thải được xử lý...). Ghi rõ đơn vị.
5. Xác định các loại nguồn bắt buộc phải có và số lượng tối thiểu cho mỗi loại.
6. Nêu giả thuyết ban đầu — và nhớ rằng giả thuyết có thể bị dữ liệu bác bỏ.
7. Nêu rủi ro của nghiên cứu này (dữ liệu cũ, dữ liệu không công bố, số liệu mâu thuẫn...).

Trả về đúng schema JSON được yêu cầu."""


def run(ctx: Ctx) -> dict[str, Any]:
    ctx.log("  · lập kế hoạch nghiên cứu (không tra web)")
    return ctx.client.json(
        system=RESEARCHER_SYSTEM,
        prompt=PROMPT.format(brief=topic_brief(ctx.topic)),
        schema=RESEARCH_PLAN,
        effort=ctx.effort("research_plan"),
    )


STAGE = Stage(
    num=1,
    key="research_plan",
    title="Research Plan",
    run=run,
    description="Câu hỏi nghiên cứu, chỉ số cần đo, yêu cầu về nguồn",
)
