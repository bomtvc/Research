"""Stage 10 — FACT CHECK: kiểm chứng lại các khẳng định, có tra web độc lập."""
from __future__ import annotations

from typing import Any

from ..base import Ctx, Stage, REVIEWER_SYSTEM, dump, topic_brief
from ..schemas import FACT_CHECK

RESEARCH_PROMPT = """{brief}

# BẢN THẢO CẦN KIỂM CHỨNG
{draft}

# MA TRẬN BẰNG CHỨNG (căn cứ nội bộ)
{matrix}

# NHIỆM VỤ
Kiểm chứng sự thật cho bản thảo. Khác với bước kiểm toán trích dẫn (chỉ soi hình thức),
bước này phải hỏi: điều này có ĐÚNG không?

Cách làm:
1. Lọc ra mọi khẳng định kiểm chứng được: số liệu, mốc thời gian, tên văn bản pháp luật,
   con số quy chuẩn, tuyên bố về chính sách đã ban hành, so sánh giữa các địa phương.
2. Với các khẳng định quan trọng nhất (ít nhất {min_checks} khẳng định), dùng web_search và
   web_fetch để kiểm tra lại bằng nguồn độc lập với nguồn đã dùng khi viết.
   Đặc biệt chú ý: số quy chuẩn kỹ thuật, tên/số hiệu và năm ban hành của văn bản pháp luật,
   và mọi con số "vượt bao nhiêu lần".
3. Phân loại: đúng / đúng một phần / sai / không kiểm chứng được.
4. Với mỗi trường hợp không phải "đúng", viết chính xác câu sửa lại nên dùng.

Đừng ngại kết luận "sai" — phát hiện sai ở bước này rẻ hơn nhiều so với phát hiện sau khi công bố."""

EXTRACT_PROMPT = """Chuyển kết quả kiểm chứng thành JSON theo schema.

Quy tắc:
- id dạng F01, F02, ...
- `statement` trích nguyên văn câu trong bản thảo.
- `correction` để trống nếu verdict là "đúng"; nếu không, phải viết câu thay thế cụ thể.
- `blocking_issues`: những lỗi mà nếu không sửa thì không được phép xuất bản bài."""


def run(ctx: Ctx) -> dict[str, Any]:
    draft = ctx.state.read_text("draft.md")
    matrix = ctx.artifact("evidence_matrix")
    ctx.log("  · kiểm chứng độc lập (có tra web)")

    data, report, _ = ctx.client.research_json(
        system=REVIEWER_SYSTEM,
        research_prompt=RESEARCH_PROMPT.format(
            brief=topic_brief(ctx.topic),
            draft=draft,
            matrix=dump(matrix.get("rows", []), limit=50_000),
            min_checks=ctx.topic.get("min_fact_checks", 12),
        ),
        extract_prompt=EXTRACT_PROMPT,
        schema=FACT_CHECK,
        effort=ctx.effort("fact_check"),
        max_searches=ctx.topic.get("max_searches", 16),
        max_fetches=ctx.topic.get("max_fetches", 12),
    )

    ctx.state.write_text("10_factcheck_report.md", report, folder="raw")
    summary = data.get("summary", {})
    ctx.log("  · " + str(summary.get("total", 0)) + " khẳng định: "
            + str(summary.get("unsupported", 0)) + " sai, "
            + str(summary.get("partial", 0)) + " đúng một phần")
    return data


STAGE = Stage(
    num=10,
    key="fact_check",
    title="Fact Check",
    run=run,
    description="Tra lại bằng nguồn độc lập, phân loại đúng/sai/không kiểm chứng được",
)
