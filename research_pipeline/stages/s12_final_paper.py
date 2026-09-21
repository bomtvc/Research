"""Stage 12 — FINAL PAPER: áp dụng toàn bộ sửa đổi, xuất bài hoàn chỉnh."""
from __future__ import annotations

from typing import Any

from ..base import Ctx, Stage, WRITER_SYSTEM, dump, topic_brief
from .. import config
from ..schemas import REVISION_LOG

REVISE_PROMPT = """{brief}

# BẢN THẢO HIỆN TẠI
{draft}

# LỖI TRÍCH DẪN PHẢI SỬA
{citation_issues}

# LỖI SỰ THẬT PHẢI SỬA
{fact_issues}

# YÊU CẦU SỬA TỪ PHẢN BIỆN
{revisions}

# DANH MỤC TÀI LIỆU THAM KHẢO ĐÃ CHUẨN HOÁ
{bibliography}

# NHIỆM VỤ
Xuất bản cuối cùng của bài nghiên cứu, đã áp dụng mọi sửa đổi ở trên.

Quy tắc:
- Sửa đúng chỗ được chỉ ra. Không viết lại những đoạn không có lỗi.
- Với mỗi khẳng định bị đánh dấu sai hoặc đúng một phần: thay bằng câu sửa đã đề xuất,
  hoặc bỏ hẳn khẳng định đó nếu không có bằng chứng thay thế. Không "làm mềm" câu sai để giữ lại.
- Không thêm bất kỳ số liệu hay nguồn nào chưa từng xuất hiện trong bản thảo và danh mục nguồn.
- Giữ nguyên cấu trúc mục của bản thảo, trừ khi phản biện yêu cầu đổi.
- Bổ sung ở cuối bài, theo thứ tự:
  1. mục "Hạn chế của nghiên cứu" — nêu thật những khoảng trống dữ liệu và điều chưa kết luận được;
  2. mục "Tài liệu tham khảo" — dùng đúng danh mục đã chuẩn hoá ở trên.
- Mở đầu bài bằng tiêu đề Markdown cấp 1, sau đó là một đoạn tóm tắt (abstract) khoảng 150–200 từ.

Chỉ trả về nội dung Markdown của bài hoàn chỉnh, không thêm lời dẫn."""

LOG_PROMPT = """Dưới đây là danh sách yêu cầu sửa và bài viết cuối cùng.

# YÊU CẦU SỬA
{requests}

# BÀI CUỐI
{final}

Lập nhật ký chỉnh sửa: mục nào đã được áp dụng (kèm mô tả thay đổi thực tế trong bài),
mục nào bị bỏ qua và vì sao, và những hạn chế còn lại của bài. Trung thực — nếu một yêu cầu
không được phản ánh trong bài cuối, hãy xếp nó vào `skipped`."""


def run(ctx: Ctx) -> dict[str, Any]:
    draft = ctx.state.read_text("draft.md")
    citation = ctx.artifact("citation_audit")
    factcheck = ctx.artifact("fact_check")
    review = ctx.artifact("peer_review")

    citation_issues = [i for i in citation.get("issues", [])
                       if i.get("severity") in ("nghiêm trọng", "trung bình")]
    fact_issues = [c for c in factcheck.get("checks", [])
                   if c.get("verdict") != "đúng"]
    revisions = [r for r in review.get("required_revisions", [])
                 if r.get("priority") in ("phải sửa", "nên sửa")]

    ctx.log("  · áp dụng " + str(len(citation_issues)) + " sửa trích dẫn, "
            + str(len(fact_issues)) + " sửa sự thật, "
            + str(len(revisions)) + " yêu cầu phản biện")

    final = ctx.client.text(
        system=WRITER_SYSTEM,
        prompt=REVISE_PROMPT.format(
            brief=topic_brief(ctx.topic),
            draft=draft,
            citation_issues=dump(citation_issues) or "(không có)",
            fact_issues=dump(fact_issues) or "(không có)",
            revisions=dump(revisions) or "(không có)",
            bibliography=dump(citation.get("bibliography", [])),
        ),
        effort=ctx.effort("final_paper"),
        max_tokens=config.MAX_TOKENS_PAPER,
    )

    path = ctx.state.write_text("final_paper.md", final)
    ctx.log("  · bài hoàn chỉnh " + str(len(final.split())) + " từ -> " + str(path))

    log = ctx.client.json(
        system=WRITER_SYSTEM,
        prompt=LOG_PROMPT.format(
            requests=dump({"citation": citation_issues, "facts": fact_issues,
                           "review": revisions}),
            final=final,
        ),
        schema=REVISION_LOG,
        effort="high",
    )
    ctx.state.write_text(
        "revision_log.md",
        "# Nhật ký chỉnh sửa\n\n```json\n" + dump(log) + "\n```\n",
    )

    return {
        "final_file": "paper/final_paper.md",
        "word_count": len(final.split()),
        "decision_before_revision": review.get("decision"),
        "revision_log": log,
    }


STAGE = Stage(
    num=12,
    key="final_paper",
    title="Final Paper",
    run=run,
    description="Áp dụng sửa đổi, thêm hạn chế + tài liệu tham khảo, xuất bài",
)
