"""Bộ điều phối: chạy tuần tự 12 stage, ghi artifact, cho phép resume."""
from __future__ import annotations

import time
import traceback
from typing import Any

from .base import Ctx
from .client import PipelineError, ResearchClient
from .stages import STAGES
from .state import RunState


def log(message: str) -> None:
    print(message, flush=True)


def run_pipeline(state: RunState, topic: dict[str, Any], client: ResearchClient,
                 start: int = 1, end: int = 12, force: bool = False) -> bool:
    """Chạy pipeline từ stage `start` tới `end`. Trả về True nếu chạy hết không lỗi."""
    ctx = Ctx(client=client, state=state, topic=topic, log=log)
    selected = [s for s in STAGES if start <= s.num <= end]

    log("")
    log("ĐỀ TÀI : " + topic["title"])
    log("RUN DIR: " + str(state.root))
    log("MODEL  : " + client.model)
    log("STAGES : " + str(start) + " → " + str(end))
    log("")

    for stage in selected:
        header = "[" + f"{stage.num:02d}" + "/12] " + stage.title
        if state.has(stage.num, stage.key) and not force:
            log(header + " — đã có artifact, bỏ qua (dùng --force để chạy lại)")
            continue

        log(header + " — " + stage.description)
        before = client.ledger.snapshot()
        started = time.time()
        try:
            data = stage.run(ctx)
        except PipelineError as exc:
            elapsed = time.time() - started
            state.record(stage.num, stage.key, stage.title, "failed", elapsed,
                         client.ledger.diff(before), str(exc))
            log("  ✗ DỪNG: " + str(exc))
            log("  → sửa xong chạy lại với: --run \"" + str(state.root) + "\"")
            return False
        except Exception as exc:  # noqa: BLE001 - muốn ghi lại mọi lỗi lạ vào manifest
            elapsed = time.time() - started
            state.record(stage.num, stage.key, stage.title, "error", elapsed,
                         client.ledger.diff(before), repr(exc))
            log("  ✗ LỖI KHÔNG LƯỜNG TRƯỚC: " + repr(exc))
            traceback.print_exc()
            return False

        elapsed = time.time() - started
        usage = client.ledger.diff(before)
        state.write(stage.num, stage.key, data)
        state.record(stage.num, stage.key, stage.title, "done", elapsed, usage)
        log("  ✓ " + f"{elapsed:.0f}" + "s · " + f"{usage['output_tokens']:,}"
            + " output token · ~$" + f"{usage['cost_usd_est']:.2f}")

    totals = state.totals()
    log("")
    log("HOÀN TẤT · tổng ~" + f"{totals['seconds'] / 60:.1f}" + " phút · ước tính ~$"
        + f"{totals['cost_usd_est']:.2f}")
    paper = state.paper_dir / "final_paper.md"
    if paper.exists():
        log("BÀI CUỐI: " + str(paper))
    return True
