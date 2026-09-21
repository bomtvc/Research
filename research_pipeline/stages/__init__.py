"""Đăng ký 12 stage theo đúng thứ tự pipeline."""
from __future__ import annotations

from ..base import Stage
from .s01_research_plan import STAGE as S01
from .s02_source_discovery import STAGE as S02
from .s03_source_verify import STAGE as S03
from .s04_evidence_matrix import STAGE as S04
from .s05_data_analysis import STAGE as S05
from .s06_argument_map import STAGE as S06
from .s07_outline import STAGE as S07
from .s08_writing import STAGE as S08
from .s09_citation_audit import STAGE as S09
from .s10_fact_check import STAGE as S10
from .s11_peer_review import STAGE as S11
from .s12_final_paper import STAGE as S12

STAGES: list[Stage] = [S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12]

__all__ = ["STAGES"]
