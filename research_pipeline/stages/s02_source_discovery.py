"""Stage 2 — SOURCE DISCOVERY: tra web để gom nguồn ứng viên."""
from __future__ import annotations

from typing import Any

from ..base import Ctx, Stage, RESEARCHER_SYSTEM, dump, topic_brief
from ..schemas import SOURCE_DISCOVERY

RESEARCH_PROMPT = """{brief}

# KẾ HOẠCH NGHIÊN CỨU ĐÃ DUYỆT
{plan}

# NHIỆM VỤ
Dùng web_search và web_fetch để tìm nguồn trả lời được các câu hỏi nghiên cứu trên.

Cách làm:
- Tìm bằng cả tiếng Việt lẫn tiếng Anh. Truy vấn tiếng Việt thường ra báo cáo trong nước;
  truy vấn tiếng Anh thường ra nghiên cứu bình duyệt và báo cáo của tổ chức quốc tế.
- Ưu tiên: báo cáo hiện trạng môi trường quốc gia và cấp tỉnh, số liệu quan trắc, niên giám
  thống kê, nghiên cứu bình duyệt, báo cáo của tổ chức quốc tế, văn bản quy phạm pháp luật
  và quy chuẩn kỹ thuật quốc gia liên quan.
- Với mỗi nguồn tiềm năng, mở nội dung ra (web_fetch) để xác nhận nó thật sự chứa số liệu,
  thay vì chỉ đọc đoạn trích trong kết quả tìm kiếm.
- Ghi lại các số liệu cụ thể mà nguồn đó chứa (giá trị, đơn vị, năm) — càng chi tiết càng tốt,
  vì bước sau sẽ dựng ma trận bằng chứng từ đây.
- Mục tiêu: ít nhất {min_sources} nguồn dùng được, cân đối giữa mảng không khí và mảng nước,
  cộng thêm nguồn cho phần giải pháp/chính sách.

Sau khi tra cứu, viết một báo cáo tra cứu liệt kê từng nguồn: tiêu đề, cơ quan/tác giả, URL,
năm, loại nguồn, và các số liệu cụ thể tìm thấy. Nếu một mảng nào đó thiếu nguồn, nói rõ."""

EXTRACT_PROMPT = """Chuyển báo cáo tra cứu dưới đây thành danh mục nguồn có cấu trúc.

Quy tắc:
- Mỗi nguồn một id dạng S01, S02, ... theo thứ tự xuất hiện.
- `url` phải là URL thật đã xuất hiện trong phiên tra cứu; không tự chế URL.
- `key_data_points` ghi lại số liệu cụ thể kèm đơn vị và năm, viết ngắn gọn.
- `coverage_gaps` liệt kê những câu hỏi nghiên cứu hiện chưa có nguồn nào phủ được."""


def run(ctx: Ctx) -> dict[str, Any]:
    plan = ctx.artifact("research_plan")
    min_sources = ctx.topic.get("min_sources", 14)
    ctx.log("  · tra web tìm nguồn (mục tiêu >= " + str(min_sources) + " nguồn)")

    data, report, raw_sources = ctx.client.research_json(
        system=RESEARCHER_SYSTEM,
        research_prompt=RESEARCH_PROMPT.format(
            brief=topic_brief(ctx.topic),
            plan=dump(plan),
            min_sources=min_sources,
        ),
        extract_prompt=EXTRACT_PROMPT,
        schema=SOURCE_DISCOVERY,
        effort=ctx.effort("source_discovery"),
        max_searches=ctx.topic.get("max_searches", 16),
        max_fetches=ctx.topic.get("max_fetches", 12),
    )

    ctx.state.write_text("02_discovery_report.md", report, folder="raw")
    data["_visited_urls"] = [s["url"] for s in raw_sources if s["url"]]
    ctx.log("  · thu được " + str(len(data.get("sources", []))) + " nguồn ứng viên")
    return data


STAGE = Stage(
    num=2,
    key="source_discovery",
    title="Source Discovery",
    run=run,
    description="Tra web, gom nguồn ứng viên kèm số liệu thô",
)
