"""Stage 7 — OUTLINE: dàn ý có phân bổ số từ và gắn sẵn bằng chứng cho từng mục."""
from __future__ import annotations

from typing import Any

from ..base import Ctx, Stage, ANALYST_SYSTEM, dump, topic_brief
from ..schemas import OUTLINE

PROMPT = """{brief}

# BẢN ĐỒ LẬP LUẬN
{argmap}

# PHÁT HIỆN
{findings}

# NHIỆM VỤ
Lập dàn ý chi tiết cho bài viết dài khoảng {target_words} từ.

Yêu cầu:
1. Cấu trúc chuẩn bài nghiên cứu: mở đầu (bối cảnh + luận đề), phương pháp và nguồn dữ liệu,
   hiện trạng ô nhiễm không khí, hiện trạng ô nhiễm nước, nguyên nhân, hậu quả,
   đánh giá các giải pháp đang triển khai, khuyến nghị, kết luận, hạn chế của nghiên cứu.
   Điều chỉnh nếu bằng chứng đòi hỏi cấu trúc khác — nhưng phải giữ mục "hạn chế".
2. Mỗi mục phải ghi rõ: mục đích của mục đó trong mạch lập luận, các ý chính,
   id luận điểm và id dòng bằng chứng sẽ dùng.
3. Phân bổ `target_words` cho từng mục, tổng xấp xỉ {target_words} từ.
   Phần hiện trạng và phần giải pháp nên chiếm tỷ trọng lớn nhất.
4. Mục nào không có bằng chứng gắn vào thì phải bỏ hoặc gộp — không giữ mục rỗng.
5. `notes`: cảnh báo cho người viết (chỗ nào dễ viết quá tay so với bằng chứng).

Trả về đúng schema JSON."""


def run(ctx: Ctx) -> dict[str, Any]:
    argmap = ctx.artifact("argument_map")
    analysis = ctx.artifact("data_analysis")
    target = ctx.topic.get("target_words", 4000)
    ctx.log("  · lập dàn ý cho bài ~" + str(target) + " từ")

    data = ctx.client.json(
        system=ANALYST_SYSTEM,
        prompt=PROMPT.format(
            brief=topic_brief(ctx.topic),
            argmap=dump(argmap),
            findings=dump(analysis.get("findings", [])),
            target_words=target,
        ),
        schema=OUTLINE,
        effort=ctx.effort("outline"),
    )
    ctx.log("  · " + str(len(data.get("sections", []))) + " mục")
    return data


STAGE = Stage(
    num=7,
    key="outline",
    title="Outline",
    run=run,
    description="Dàn ý có ngân sách từ và bằng chứng gắn sẵn",
)
