"""Stage 11 — PEER REVIEW: phản biện toàn bài như một người bình duyệt."""
from __future__ import annotations

from typing import Any

from ..base import Ctx, Stage, REVIEWER_SYSTEM, dump, topic_brief
from ..schemas import PEER_REVIEW

PROMPT = """{brief}

# BẢN THẢO
{draft}

# BẢN ĐỒ LẬP LUẬN (điều bài viết lẽ ra phải chứng minh)
{argmap}

# KẾT QUẢ KIỂM TOÁN TRÍCH DẪN
{citation}

# KẾT QUẢ KIỂM CHỨNG SỰ THẬT
{factcheck}

# NHIỆM VỤ
Phản biện bản thảo như một người bình duyệt độc lập. Chấm điểm 1–5 cho từng tiêu chí:

1. Độ vững của bằng chứng — kết luận có tương xứng với dữ liệu không?
2. Chất lượng lập luận — có nhảy bước, khái quát hoá quá mức, nhầm tương quan thành nhân quả?
3. Bao phủ đề tài — đã trả lời đủ câu hỏi nghiên cứu chưa? Có mảng nào bị viết qua loa?
4. Tính khả thi của giải pháp — giải pháp có gắn với nguyên nhân đã chứng minh, có cụ thể,
   có chủ thể thực hiện không? Hay chỉ là khẩu hiệu?
5. Tính trung thực — bài có thừa nhận giới hạn dữ liệu, có nêu mâu thuẫn giữa các nguồn không?
6. Cấu trúc và văn phong học thuật.

Sau đó liệt kê `required_revisions`: những sửa đổi bắt buộc, mỗi mục nêu rõ vị trí, vấn đề,
và hành động sửa cụ thể. Gộp cả lỗi nghiêm trọng từ hai bước kiểm tra phía trên vào đây,
để bước cuối chỉ cần làm theo một danh sách duy nhất.

Quyết định: chấp nhận / chấp nhận sau chỉnh sửa nhỏ / sửa lớn rồi xét lại.
Đừng dễ dãi: nếu bài còn khẳng định không có bằng chứng, không được chấp nhận."""


def run(ctx: Ctx) -> dict[str, Any]:
    draft = ctx.state.read_text("draft.md")
    ctx.log("  · phản biện toàn bài")

    data = ctx.client.json(
        system=REVIEWER_SYSTEM,
        prompt=PROMPT.format(
            brief=topic_brief(ctx.topic),
            draft=draft,
            argmap=dump(ctx.artifact("argument_map")),
            citation=dump(ctx.artifact("citation_audit")),
            factcheck=dump(ctx.artifact("fact_check")),
        ),
        schema=PEER_REVIEW,
        effort=ctx.effort("peer_review"),
    )

    must_fix = [r for r in data.get("required_revisions", []) if r.get("priority") == "phải sửa"]
    ctx.log("  · quyết định: " + str(data.get("decision"))
            + " — " + str(len(must_fix)) + " mục phải sửa")
    return data


STAGE = Stage(
    num=11,
    key="peer_review",
    title="Peer Review",
    run=run,
    description="Chấm điểm 6 tiêu chí, ra danh sách sửa đổi bắt buộc",
)
