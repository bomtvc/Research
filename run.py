#!/usr/bin/env python
"""CLI cho Research Pipeline.

Ví dụ:
    python run.py --topic topics/hcmc_pollution.yaml
    python run.py --run runs/thuc-trang-o-nhiem-...-20260921-2115          # chạy tiếp
    python run.py --run runs/... --from 8 --force                          # viết lại từ stage 8
    python run.py --list
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from research_pipeline import config
from research_pipeline.client import ResearchClient
from research_pipeline.pipeline import log, run_pipeline
from research_pipeline.stages import STAGES
from research_pipeline.state import RunState

ROOT = Path(__file__).resolve().parent
RUNS_DIR = ROOT / "runs"


def load_topic(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not data or "title" not in data:
        raise SystemExit("File đề tài phải có ít nhất trường `title`: " + str(path))
    return data


def main() -> int:
    # Console Windows mặc định là cp1252 -> tiếng Việt sẽ crash khi in.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        description="Research Pipeline — 12 bước từ đề tài tới bài hoàn chỉnh.")
    parser.add_argument("--topic", type=Path, help="File YAML mô tả đề tài (chạy mới)")
    parser.add_argument("--run", type=Path, help="Thư mục run có sẵn (chạy tiếp/chạy lại)")
    parser.add_argument("--from", dest="start", type=int, default=1, help="Stage bắt đầu (1-12)")
    parser.add_argument("--to", dest="end", type=int, default=12, help="Stage kết thúc (1-12)")
    parser.add_argument("--only", type=int, help="Chỉ chạy đúng một stage")
    parser.add_argument("--force", action="store_true",
                        help="Chạy lại cả khi artifact đã tồn tại")
    parser.add_argument("--model", default=config.MODEL, help="Model id (mặc định " + config.MODEL + ")")
    parser.add_argument("--echo", action="store_true", help="In nội dung model sinh ra theo thời gian thực")
    parser.add_argument("--list", action="store_true", help="Liệt kê 12 stage rồi thoát")
    args = parser.parse_args()

    if args.list:
        for stage in STAGES:
            print(f"{stage.num:2d}. {stage.title:<18} {stage.description}")
        return 0

    if args.only:
        args.start = args.end = args.only

    if args.run:
        state = RunState.resume(args.run)
        topic = state.manifest["topic"]
    elif args.topic:
        topic = load_topic(args.topic)
        state = RunState.create(topic, RUNS_DIR)
    else:
        parser.error("Cần --topic (chạy mới) hoặc --run (chạy tiếp). Xem --help.")
        return 2

    client = ResearchClient(model=args.model, log=log, echo=args.echo)
    ok = run_pipeline(state, topic, client,
                      start=args.start, end=args.end, force=args.force)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
