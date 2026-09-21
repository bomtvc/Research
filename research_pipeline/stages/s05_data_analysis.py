"""Stage 5 — DATA ANALYSIS: từ số liệu rời rạc thành phát hiện có ý nghĩa."""
from __future__ import annotations

from typing import Any

from ..base import Ctx, Stage, ANALYST_SYSTEM, dump, topic_brief
from ..schemas import DATA_ANALYSIS

PROMPT = """{brief}

# CÂU HỎI NGHIÊN CỨU
{questions}

# MA TRẬN BẰNG CHỨNG
{matrix}

# NHIỆM VỤ
Phân tích ma trận bằng chứng trên. Bạn KHÔNG được thêm số liệu mới; chỉ làm việc với các dòng đã có.

Yêu cầu:
1. Rút ra các phát hiện (findings). Mỗi phát hiện phải dẫn id dòng bằng chứng cụ thể.
   Phát hiện là một mệnh đề có nội dung ("nồng độ X vượt quy chuẩn Y lần trong giai đoạn Z"),
   không phải mô tả lại bảng số liệu.
2. Với mỗi phát hiện: xu hướng, độ lớn, và "so what" — vì sao con số này đáng quan tâm
   (đối chiếu quy chuẩn, đối chiếu ngưỡng khuyến nghị quốc tế, hoặc so với địa phương khác
   nếu ma trận có dữ liệu đó).
3. So sánh: giữa hai mảng không khí và nước, giữa các năm, giữa các khu vực — chỉ khi bằng chứng
   cho phép so sánh cùng đơn vị và cùng phương pháp đo. Nếu không so sánh được, nói rõ tại sao.
4. Nguyên nhân: liệt kê các yếu tố tác động, nêu cơ chế, và mức độ chắc chắn. Phân biệt rõ
   "có tương quan trong dữ liệu" với "đã được chứng minh là nguyên nhân".
5. Nêu khoảng trống còn lại và ảnh hưởng của chúng tới kết luận.

Trả về đúng schema JSON."""


def run(ctx: Ctx) -> dict[str, Any]:
    plan = ctx.artifact("research_plan")
    matrix = ctx.artifact("evidence_matrix")
    ctx.log("  · phân tích " + str(len(matrix.get("rows", []))) + " dòng bằng chứng")

    data = ctx.client.json(
        system=ANALYST_SYSTEM,
        prompt=PROMPT.format(
            brief=topic_brief(ctx.topic),
            questions=dump(plan.get("research_questions", [])),
            matrix=dump(matrix),
        ),
        schema=DATA_ANALYSIS,
        effort=ctx.effort("data_analysis"),
    )
    ctx.log("  · rút ra " + str(len(data.get("findings", []))) + " phát hiện")
    return data


STAGE = Stage(
    num=5,
    key="data_analysis",
    title="Data Analysis",
    run=run,
    description="Xu hướng, so sánh, nguyên nhân — đều neo vào id bằng chứng",
)
