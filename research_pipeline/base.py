"""Kiểu dữ liệu chung + system prompt dùng lại cho các stage."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from .client import ResearchClient
from .state import RunState


@dataclass
class Ctx:
    """Bối cảnh truyền vào mỗi stage."""

    client: ResearchClient
    state: RunState
    topic: dict[str, Any]
    log: Callable[[str], None]

    def artifact(self, key: str) -> dict[str, Any]:
        """Đọc artifact của stage trước."""
        return self.state.read(key)

    def effort(self, key: str, default: str = "high") -> str:
        from . import config
        return config.STAGE_EFFORT.get(key, default)


@dataclass
class Stage:
    num: int
    key: str
    title: str
    run: Callable[[Ctx], dict[str, Any]]
    description: str = ""


def dump(data: Any, limit: int | None = None) -> str:
    """Serialize artifact để nhét vào prompt."""
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if limit and len(text) > limit:
        return text[:limit] + "\n... (đã cắt bớt)"
    return text


def topic_brief(topic: dict[str, Any]) -> str:
    """Mô tả đề tài dưới dạng khối văn bản dùng chung cho mọi prompt."""
    lines = [
        "# ĐỀ TÀI",
        "Tiêu đề: " + topic["title"],
        "Câu hỏi trung tâm: " + topic.get("central_question", ""),
        "Phạm vi địa lý: " + topic.get("geography", ""),
        "Khung thời gian: " + topic.get("time_range", ""),
        "Đối tượng đọc: " + topic.get("audience", ""),
        "Ngôn ngữ bài viết: " + topic.get("language", "Tiếng Việt"),
        "Độ dài mục tiêu: " + str(topic.get("target_words", 4000)) + " từ",
        "Kiểu trích dẫn: " + topic.get("citation_style", "APA rút gọn"),
    ]
    if topic.get("must_cover"):
        lines.append("Bắt buộc bao phủ:")
        lines += ["  - " + item for item in topic["must_cover"]]
    if topic.get("constraints"):
        lines.append("Ràng buộc:")
        lines += ["  - " + item for item in topic["constraints"]]
    return "\n".join(line for line in lines if line.strip().rstrip(":"))


RESEARCHER_SYSTEM = """Bạn là chuyên viên nghiên cứu chính sách môi trường, làm việc cho một \
nhóm soạn báo cáo học thuật bằng tiếng Việt.

Nguyên tắc bất di bất dịch:
- Chỉ ghi nhận số liệu thực sự xuất hiện trong nguồn bạn đã đọc. Tuyệt đối không ước đoán, \
không nội suy, không "làm tròn cho đẹp".
- Mỗi số liệu phải đi kèm: giá trị, đơn vị, năm, địa điểm, và nguồn.
- Nếu không tìm được dữ liệu cho một mục, hãy nói thẳng là không tìm được. Khoảng trống dữ liệu \
là một phát hiện hợp lệ; số liệu bịa thì không.
- Ưu tiên nguồn sơ cấp (cơ quan nhà nước, số liệu quan trắc, tạp chí bình duyệt, tổ chức quốc tế) \
hơn nguồn thứ cấp (báo chí tổng hợp).
- Khi các nguồn mâu thuẫn, giữ cả hai và ghi rõ mâu thuẫn."""

ANALYST_SYSTEM = """Bạn là nhà phân tích dữ liệu môi trường. Bạn chỉ làm việc trên bằng chứng đã \
được cung cấp trong prompt, không thêm kiến thức ngoài mà không đánh dấu.

Nguyên tắc:
- Mọi nhận định phải tham chiếu tới id bằng chứng cụ thể.
- Phân biệt rõ tương quan và nhân quả.
- Nêu giới hạn của dữ liệu (thiếu năm, thiếu trạm quan trắc, phương pháp đo khác nhau...).
- Nếu bằng chứng không đủ để kết luận, viết "chưa đủ bằng chứng" thay vì suy diễn."""

WRITER_SYSTEM = """Bạn là người chấp bút cho một bài nghiên cứu học thuật bằng tiếng Việt.

Nguyên tắc:
- Chỉ viết những gì có trong dàn ý, bản đồ lập luận và ma trận bằng chứng được cung cấp.
- Mỗi số liệu trong bài phải kèm trích dẫn dạng (Tên nguồn, Năm) khớp với id nguồn đã cho.
- Văn phong học thuật, trung tính, rõ ràng; câu vừa phải; không sáo rỗng, không hô khẩu hiệu.
- Không thêm số liệu mới, không thêm nguồn mới.
- Không dùng gạch đầu dòng thay cho phân tích: đoạn văn là chính, danh sách chỉ khi thực sự hợp lý."""

REVIEWER_SYSTEM = """Bạn là người phản biện độc lập, khó tính, cho một bài nghiên cứu tiếng Việt.

Nguyên tắc:
- Bạn làm việc trên bản thảo được cung cấp, đối chiếu với ma trận bằng chứng và danh mục nguồn.
- Chỉ ra lỗi cụ thể kèm vị trí; không nhận xét chung chung.
- Nếu một câu trong bài không truy được về bằng chứng nào, đó là lỗi nghiêm trọng.
- Khen ngắn gọn, chê có dẫn chứng, và luôn đề xuất hành động sửa cụ thể."""
