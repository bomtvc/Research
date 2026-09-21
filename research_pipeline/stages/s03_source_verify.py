"""Stage 3 — SOURCE VERIFY: sàng nguồn, loại nguồn yếu trước khi trích dẫn."""
from __future__ import annotations

from typing import Any

from ..base import Ctx, Stage, RESEARCHER_SYSTEM, dump, topic_brief
from ..schemas import SOURCE_VERIFY

RESEARCH_PROMPT = """{brief}

# DANH MỤC NGUỒN ỨNG VIÊN
{sources}

# NHIỆM VỤ
Thẩm định từng nguồn trước khi cho phép trích dẫn. Với mỗi nguồn, xét bốn tiêu chí:

1. Thẩm quyền — ai công bố? Cơ quan quản lý, nhóm nghiên cứu, hay trang tổng hợp lại tin?
   Nguồn thứ cấp dẫn lại số liệu của nơi khác thì phải truy về nguồn gốc.
2. Tính cập nhật — số liệu thuộc năm nào? So với khung thời gian của đề tài, còn dùng được không?
   Số liệu cũ vẫn dùng được nếu dùng để so sánh xu hướng, nhưng phải ghi rõ là số liệu cũ.
3. Tính kiểm chứng — URL có mở được không? Số liệu có nêu phương pháp đo, vị trí trạm quan trắc,
   cỡ mẫu không? Dùng web_fetch để mở lại những nguồn quan trọng và xác nhận.
4. Thiên lệch — nguồn có lợi ích trong kết luận không? Ngôn ngữ có mang tính vận động không?

Xếp hạng: A = cơ quan/dữ liệu sơ cấp/bình duyệt; B = tổ chức uy tín hoặc báo chí có dẫn nguồn gốc;
C = chỉ dùng để minh hoạ, không dùng làm căn cứ số liệu.

Loại thẳng nguồn nào: không mở được, không truy ra số liệu gốc, hoặc chỉ là bài tổng hợp lại
mà không nêu nguồn.

Viết kết quả thẩm định cho từng nguồn theo id."""

EXTRACT_PROMPT = """Chuyển kết quả thẩm định thành JSON theo schema.

Quy tắc:
- Mỗi nguồn trong danh mục ứng viên phải có đúng một phán quyết, dùng đúng id cũ.
- `accepted_ids` gồm nguồn hạng A và B được chấp nhận (kể cả chấp nhận có điều kiện).
- `rejected_ids` gồm nguồn bị loại. Nêu lý do trong `concerns`.
- `summary` nói rõ: còn bao nhiêu nguồn dùng được, mảng nào đang yếu."""


def run(ctx: Ctx) -> dict[str, Any]:
    discovery = ctx.artifact("source_discovery")
    sources = discovery.get("sources", [])
    ctx.log("  · thẩm định " + str(len(sources)) + " nguồn")

    data, report, _ = ctx.client.research_json(
        system=RESEARCHER_SYSTEM,
        research_prompt=RESEARCH_PROMPT.format(
            brief=topic_brief(ctx.topic),
            sources=dump(sources),
        ),
        extract_prompt=EXTRACT_PROMPT,
        schema=SOURCE_VERIFY,
        effort=ctx.effort("source_verify"),
        max_searches=6,
        max_fetches=ctx.topic.get("max_fetches", 12),
    )

    ctx.state.write_text("03_verify_report.md", report, folder="raw")
    accepted = data.get("accepted_ids", [])
    ctx.log("  · còn lại " + str(len(accepted)) + " nguồn được chấp nhận")
    if len(accepted) < ctx.topic.get("min_accepted_sources", 8):
        ctx.log("  · CẢNH BÁO: số nguồn đạt chuẩn thấp, bài viết sẽ mỏng bằng chứng")
    return data


STAGE = Stage(
    num=3,
    key="source_verify",
    title="Source Verify",
    run=run,
    description="Thẩm quyền, tính cập nhật, tính kiểm chứng, thiên lệch",
)
