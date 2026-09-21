"""Stage 6 — ARGUMENT MAP: luận điểm, căn cứ, phản biện, và luận điểm giải pháp."""
from __future__ import annotations

from typing import Any

from ..base import Ctx, Stage, ANALYST_SYSTEM, dump, topic_brief
from ..schemas import ARGUMENT_MAP

PROMPT = """{brief}

# PHÁT HIỆN TỪ PHÂN TÍCH
{analysis}

# MA TRẬN BẰNG CHỨNG (rút gọn)
{matrix}

# NHIỆM VỤ
Dựng bản đồ lập luận cho bài viết.

Yêu cầu:
1. Một luận đề (thesis) duy nhất cho toàn bài: một mệnh đề có thể bị phản bác, không phải
   một mô tả trung tính. Luận đề phải nói được cả hiện trạng lẫn hướng xử lý.
2. Các luận điểm về hiện trạng và nguyên nhân. Mỗi luận điểm gồm:
   - claim: điều muốn chứng minh;
   - grounds: các bằng chứng cụ thể (dẫn id phát hiện / id dòng bằng chứng);
   - warrant: vì sao bằng chứng đó đủ để suy ra claim — đây là chỗ hay bị bỏ qua nhất;
   - qualifier: giới hạn của claim ("trong giai đoạn...", "tại các trạm...");
   - rebuttal: phản biện mạnh nhất mà người đọc khó tính sẽ nêu;
   - response_to_rebuttal: trả lời phản biện đó bằng bằng chứng, hoặc thừa nhận nếu không trả lời được.
3. Các luận điểm giải pháp. Mỗi giải pháp phải gắn với một vấn đề cụ thể đã chứng minh ở trên,
   kèm tính khả thi, chi phí (nếu nguồn có đề cập), và tác động kỳ vọng. Giải pháp không gắn được
   với bằng chứng nào thì loại bỏ — không đưa giải pháp chung chung kiểu "nâng cao ý thức".
4. logic_check: tự soát xem có luận điểm nào đang nhảy bước, khái quát hoá quá mức, hoặc
   nhầm tương quan thành nhân quả không. Nói thật.

Trả về đúng schema JSON."""


def run(ctx: Ctx) -> dict[str, Any]:
    analysis = ctx.artifact("data_analysis")
    matrix = ctx.artifact("evidence_matrix")
    ctx.log("  · dựng bản đồ lập luận")

    data = ctx.client.json(
        system=ANALYST_SYSTEM,
        prompt=PROMPT.format(
            brief=topic_brief(ctx.topic),
            analysis=dump(analysis),
            matrix=dump(matrix.get("rows", []), limit=60_000),
        ),
        schema=ARGUMENT_MAP,
        effort=ctx.effort("argument_map"),
    )
    ctx.log("  · " + str(len(data.get("arguments", []))) + " luận điểm, "
            + str(len(data.get("solution_arguments", []))) + " giải pháp")
    return data


STAGE = Stage(
    num=6,
    key="argument_map",
    title="Argument Map",
    run=run,
    description="Toulmin: claim – grounds – warrant – rebuttal",
)
