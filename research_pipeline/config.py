"""Cấu hình toàn cục cho Research Pipeline."""
from __future__ import annotations

# --- Model -------------------------------------------------------------
# Opus 5: 1M context, thinking bật mặc định (adaptive), 128K output.
MODEL = "claude-opus-5"

# Effort mặc định theo từng stage (low | medium | high | xhigh | max).
# Stage suy luận nặng (phân tích, lập luận, review) để cao hơn.
STAGE_EFFORT = {
    "research_plan": "high",
    "source_discovery": "high",
    "source_verify": "high",
    "evidence_matrix": "high",
    "data_analysis": "xhigh",
    "argument_map": "xhigh",
    "outline": "high",
    "writing": "high",
    "citation_audit": "high",
    "fact_check": "xhigh",
    "peer_review": "xhigh",
    "final_paper": "xhigh",
}

# --- Token budget ------------------------------------------------------
# Luôn stream => max_tokens lớn không sợ HTTP timeout.
MAX_TOKENS_JSON = 32_000
MAX_TOKENS_TEXT = 32_000
MAX_TOKENS_PAPER = 64_000

# --- Web research ------------------------------------------------------
# Biến server tool mới (dynamic filtering) - yêu cầu Opus 4.6+/Sonnet 4.6+.
WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search"}
WEB_FETCH = {"type": "web_fetch_20260209", "name": "web_fetch"}

MAX_SEARCHES_PER_STAGE = 12
MAX_FETCHES_PER_STAGE = 10
MAX_PAUSE_TURN_RESUMES = 8

# Định vị người dùng giúp web_search ưu tiên nguồn Việt Nam.
# Nếu API trả 400 vì shape không hợp lệ, đặt USER_LOCATION = None.
USER_LOCATION = {
    "type": "approximate",
    "city": "Ho Chi Minh City",
    "country": "VN",
    "timezone": "Asia/Ho_Chi_Minh",
}

# Chặn các domain rác/nội dung tổng hợp thấp chất lượng (tùy chỉnh tự do).
BLOCKED_DOMAINS: list[str] = []

# --- Pricing (USD / 1M token) -----------------------------------------
PRICING = {
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
}
# Hệ số ước lượng cho token cache (ghi / đọc) so với giá input.
# Đây là ƯỚC LƯỢNG để hiển thị chi phí, không phải hoá đơn chính thức.
CACHE_WRITE_MULT = 1.25
CACHE_READ_MULT = 0.10
