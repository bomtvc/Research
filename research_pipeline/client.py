"""Lớp bọc Anthropic SDK: gọi JSON có schema, gọi văn bản dài, và gọi có web research."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

import anthropic

from . import config


class PipelineError(RuntimeError):
    """Lỗi không thể tiếp tục ở tầng pipeline."""


@dataclass
class Ledger:
    """Sổ ghi token + chi phí ước lượng."""

    model: str
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    def add(self, usage: Any) -> None:
        self.calls += 1
        self.input_tokens += getattr(usage, "input_tokens", 0) or 0
        self.output_tokens += getattr(usage, "output_tokens", 0) or 0
        self.cache_read_tokens += getattr(usage, "cache_read_input_tokens", 0) or 0
        self.cache_write_tokens += getattr(usage, "cache_creation_input_tokens", 0) or 0

    @property
    def cost_usd(self) -> float:
        in_rate, out_rate = config.PRICING.get(self.model, config.PRICING[config.MODEL])
        return (
            self.input_tokens * in_rate
            + self.cache_write_tokens * in_rate * config.CACHE_WRITE_MULT
            + self.cache_read_tokens * in_rate * config.CACHE_READ_MULT
            + self.output_tokens * out_rate
        ) / 1_000_000

    def snapshot(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "cost_usd_est": round(self.cost_usd, 4),
        }

    def diff(self, before: dict[str, Any]) -> dict[str, Any]:
        now = self.snapshot()
        return {
            key: (round(now[key] - before[key], 4) if isinstance(now[key], float)
                  else now[key] - before[key])
            for key in now
        }


def _text_of(message: Any) -> str:
    """Nối mọi text block; bỏ qua thinking/tool block."""
    return "\n".join(b.text for b in message.content if b.type == "text").strip()


def _first_json(message: Any) -> dict[str, Any]:
    for block in message.content:
        if block.type == "text":
            try:
                return json.loads(block.text)
            except json.JSONDecodeError:
                continue
    raise PipelineError("Không tìm thấy JSON hợp lệ trong phản hồi của model.")


def _collect_sources(message: Any) -> list[dict[str, Any]]:
    """Rút URL/tiêu đề từ các block kết quả web_search.

    Lưu ý: khi lỗi, `.content` là một object (có `error_code`) chứ không phải list.
    """
    found: list[dict[str, Any]] = []
    for block in message.content:
        if block.type != "web_search_tool_result":
            continue
        content = block.content
        if not isinstance(content, list):
            code = getattr(content, "error_code", "unknown")
            found.append({"title": "[loi web_search: " + str(code) + "]", "url": "", "page_age": None})
            continue
        for result in content:
            found.append({
                "title": getattr(result, "title", "") or "",
                "url": getattr(result, "url", "") or "",
                "page_age": getattr(result, "page_age", None),
            })
    return found


def _dedupe_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in sources:
        key = item.get("url") or item.get("title", "")
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


class ResearchClient:
    """Mọi lời gọi model trong pipeline đều đi qua đây."""

    def __init__(self, model: str = config.MODEL, log: Callable[[str], None] = print,
                 echo: bool = False) -> None:
        self.model = model
        self.client = anthropic.Anthropic(max_retries=4)
        self.ledger = Ledger(model=model)
        self.log = log
        self.echo = echo

    # -- lõi ------------------------------------------------------------
    def _stream(self, **kwargs: Any) -> Any:
        try:
            with self.client.messages.stream(model=self.model, **kwargs) as stream:
                if self.echo:
                    for chunk in stream.text_stream:
                        print(chunk, end="", flush=True)
                message = stream.get_final_message()
        except anthropic.BadRequestError as exc:
            raise PipelineError("Request bi tu choi: " + str(exc.message)) from exc
        except anthropic.AuthenticationError as exc:
            raise PipelineError(
                "Thiếu hoặc sai credential. Đặt ANTHROPIC_API_KEY hoặc chạy `ant auth login`."
            ) from exc
        except anthropic.RateLimitError as exc:
            raise PipelineError("Bi rate limit sau khi da retry: " + str(exc)) from exc

        self.ledger.add(message.usage)
        if message.stop_reason == "refusal":
            detail = getattr(message, "stop_details", None)
            category = getattr(detail, "category", None)
            raise PipelineError("Model tu choi tra loi (category=" + str(category) + ").")
        return message

    # -- API cho stage --------------------------------------------------
    def text(self, system: str, prompt: str, effort: str = "high",
             max_tokens: int = config.MAX_TOKENS_TEXT) -> str:
        """Sinh văn bản dài (draft, section, bản sửa cuối)."""
        message = self._stream(
            max_tokens=max_tokens,
            system=system,
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
            messages=[{"role": "user", "content": prompt}],
        )
        return _text_of(message)

    def json(self, system: str, prompt: str, schema: dict[str, Any], effort: str = "high",
             max_tokens: int = config.MAX_TOKENS_JSON) -> dict[str, Any]:
        """Sinh artifact có cấu trúc, ràng buộc bằng JSON Schema."""
        message = self._stream(
            max_tokens=max_tokens,
            system=system,
            thinking={"type": "adaptive"},
            output_config={"effort": effort,
                           "format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": prompt}],
        )
        return _first_json(message)

    def research(self, system: str, prompt: str, effort: str = "high",
                 max_searches: int = config.MAX_SEARCHES_PER_STAGE,
                 max_fetches: int = config.MAX_FETCHES_PER_STAGE,
                 allowed_domains: list[str] | None = None) -> tuple[str, list[dict[str, Any]]]:
        """Chạy vòng lặp server-tool (web_search + web_fetch).

        Trả về (báo cáo dạng văn bản, danh sách nguồn thô đã truy cập).
        Server tool chạy trên hạ tầng Anthropic nên không có hàm nào phải thực thi ở client;
        việc duy nhất phải làm thủ công là nối lại lượt bị `pause_turn`.
        """
        search_tool: dict[str, Any] = dict(config.WEB_SEARCH, max_uses=max_searches)
        fetch_tool: dict[str, Any] = dict(config.WEB_FETCH, max_uses=max_fetches)
        if config.USER_LOCATION:
            search_tool["user_location"] = config.USER_LOCATION
        if allowed_domains:
            search_tool["allowed_domains"] = allowed_domains
            fetch_tool["allowed_domains"] = allowed_domains
        elif config.BLOCKED_DOMAINS:
            search_tool["blocked_domains"] = config.BLOCKED_DOMAINS
            fetch_tool["blocked_domains"] = config.BLOCKED_DOMAINS

        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        sources: list[dict[str, Any]] = []
        chunks: list[str] = []
        paused = False

        for attempt in range(config.MAX_PAUSE_TURN_RESUMES + 1):
            message = self._stream(
                max_tokens=config.MAX_TOKENS_TEXT,
                system=system,
                thinking={"type": "adaptive"},
                output_config={"effort": effort},
                tools=[search_tool, fetch_tool],
                messages=messages,
            )
            sources.extend(_collect_sources(message))
            chunks.append(_text_of(message))
            messages.append({"role": "assistant", "content": message.content})
            paused = message.stop_reason == "pause_turn"
            if not paused:
                break
            self.log("    · lượt bị tạm dừng (pause_turn), nối tiếp lần " + str(attempt + 1))

        if paused:
            self.log("    · cảnh báo: vẫn pause_turn sau số lần nối tối đa, dùng kết quả hiện có")

        return "\n\n".join(c for c in chunks if c), _dedupe_sources(sources)

    def research_json(self, system: str, research_prompt: str, extract_prompt: str,
                      schema: dict[str, Any], effort: str = "high",
                      **research_kwargs: Any) -> tuple[dict[str, Any], str, list[dict[str, Any]]]:
        """Hai pha: (1) tra cứu web ở dạng văn bản, (2) trích xuất sang JSON có schema.

        Tách hai pha để không phải vừa ràng buộc schema vừa gọi tool trong cùng một lượt;
        pha trích xuất không dùng tool nên rẻ và ổn định hơn.
        """
        report, sources = self.research(system, research_prompt, effort=effort, **research_kwargs)
        if not report.strip():
            raise PipelineError("Pha tra cứu không trả về nội dung nào.")
        source_list = "\n".join("- " + s["title"] + " — " + s["url"] for s in sources) or "(không có)"
        payload = (
            extract_prompt
            + "\n\n## Báo cáo tra cứu\n" + report
            + "\n\n## Các URL đã truy cập trong phiên tra cứu\n" + source_list
        )
        data = self.json(system, payload, schema, effort="high")
        return data, report, sources
