"""JSON Schema cho artifact của từng stage.

Dùng schema thô (không qua Pydantic) để bạn sửa trực tiếp được:
mỗi object đều `additionalProperties: false` và liệt kê đủ `required`,
đúng yêu cầu của structured outputs.
"""
from __future__ import annotations

from typing import Any

STRING = {"type": "string"}
NUMBER = {"type": "number"}
INTEGER = {"type": "integer"}


def arr(items: dict[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": items}


def obj(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def enum(*values: str) -> dict[str, Any]:
    return {"type": "string", "enum": list(values)}


STR_LIST = arr(STRING)

# 1 ---------------------------------------------------------------------
RESEARCH_PLAN = obj({
    "topic_restated": STRING,
    "scope": obj({
        "geography": STRING,
        "time_range": STRING,
        "in_scope": STR_LIST,
        "out_of_scope": STR_LIST,
    }),
    "research_questions": arr(obj({
        "id": STRING,
        "question": STRING,
        "why_it_matters": STRING,
        "priority": enum("cao", "trung bình", "thấp"),
    })),
    "sub_topics": arr(obj({
        "name": STRING,
        "domain": enum("không khí", "nước", "chung", "chính sách"),
        "what_to_find": STR_LIST,
    })),
    "key_indicators": arr(obj({
        "name": STRING,
        "unit": STRING,
        "why": STRING,
    })),
    "source_requirements": arr(obj({
        "category": STRING,
        "examples": STR_LIST,
        "minimum_count": INTEGER,
    })),
    "hypotheses": STR_LIST,
    "risks": STR_LIST,
})

# 2 ---------------------------------------------------------------------
SOURCE_DISCOVERY = obj({
    "sources": arr(obj({
        "id": STRING,
        "title": STRING,
        "publisher": STRING,
        "url": STRING,
        "year": STRING,
        "type": enum("báo cáo nhà nước", "nghiên cứu khoa học", "tổ chức quốc tế",
                     "báo chí", "dữ liệu quan trắc", "luật/quy định", "khác"),
        "language": STRING,
        "covers": STR_LIST,
        "relevance": STRING,
        "key_data_points": STR_LIST,
    })),
    "coverage_gaps": STR_LIST,
})

# 3 ---------------------------------------------------------------------
SOURCE_VERIFY = obj({
    "verdicts": arr(obj({
        "source_id": STRING,
        "status": enum("chấp nhận", "chấp nhận có điều kiện", "loại"),
        "tier": enum("A", "B", "C"),
        "authority_note": STRING,
        "recency_note": STRING,
        "verifiability_note": STRING,
        "concerns": STR_LIST,
        "usable_for": STR_LIST,
    })),
    "accepted_ids": STR_LIST,
    "rejected_ids": STR_LIST,
    "summary": STRING,
})

# 4 ---------------------------------------------------------------------
EVIDENCE_MATRIX = obj({
    "rows": arr(obj({
        "id": STRING,
        "claim": STRING,
        "indicator": STRING,
        "value": STRING,
        "unit": STRING,
        "year": STRING,
        "location": STRING,
        "domain": enum("không khí", "nước", "cả hai", "chính sách"),
        "source_ids": STR_LIST,
        "confidence": enum("cao", "trung bình", "thấp"),
        "notes": STRING,
    })),
    "conflicts": arr(obj({
        "description": STRING,
        "row_ids": STR_LIST,
        "resolution": STRING,
    })),
    "gaps": STR_LIST,
})

# 5 ---------------------------------------------------------------------
DATA_ANALYSIS = obj({
    "findings": arr(obj({
        "id": STRING,
        "statement": STRING,
        "evidence_row_ids": STR_LIST,
        "trend": enum("tăng", "giảm", "đi ngang", "biến động", "không xác định"),
        "magnitude": STRING,
        "so_what": STRING,
        "caveats": STR_LIST,
    })),
    "comparisons": arr(obj({
        "description": STRING,
        "basis": STRING,
        "evidence_row_ids": STR_LIST,
    })),
    "causal_factors": arr(obj({
        "factor": STRING,
        "domain": enum("không khí", "nước", "cả hai"),
        "mechanism": STRING,
        "evidence_row_ids": STR_LIST,
        "strength": enum("mạnh", "vừa", "yếu"),
    })),
    "remaining_gaps": STR_LIST,
})

# 6 ---------------------------------------------------------------------
ARGUMENT_MAP = obj({
    "thesis": STRING,
    "arguments": arr(obj({
        "id": STRING,
        "claim": STRING,
        "grounds": STR_LIST,
        "warrant": STRING,
        "qualifier": STRING,
        "rebuttal": STRING,
        "response_to_rebuttal": STRING,
        "finding_ids": STR_LIST,
    })),
    "solution_arguments": arr(obj({
        "id": STRING,
        "solution": STRING,
        "target_problem": STRING,
        "rationale": STRING,
        "feasibility": enum("cao", "trung bình", "thấp"),
        "cost_note": STRING,
        "expected_impact": STRING,
        "evidence_row_ids": STR_LIST,
    })),
    "logic_check": STRING,
})

# 7 ---------------------------------------------------------------------
OUTLINE = obj({
    "title": STRING,
    "sections": arr(obj({
        "id": STRING,
        "heading": STRING,
        "level": INTEGER,
        "purpose": STRING,
        "key_points": STR_LIST,
        "argument_ids": STR_LIST,
        "evidence_row_ids": STR_LIST,
        "target_words": INTEGER,
    })),
    "total_target_words": INTEGER,
    "notes": STRING,
})

# 9 ---------------------------------------------------------------------
CITATION_AUDIT = obj({
    "issues": arr(obj({
        "id": STRING,
        "section_heading": STRING,
        "quoted_text": STRING,
        "type": enum("thiếu trích dẫn", "trích dẫn sai nguồn", "nguồn không tồn tại trong danh mục",
                     "sai định dạng", "số liệu không khớp nguồn"),
        "severity": enum("nghiêm trọng", "trung bình", "nhẹ"),
        "detail": STRING,
        "suggested_fix": STRING,
    })),
    "unused_sources": STR_LIST,
    "bibliography": arr(obj({
        "source_id": STRING,
        "formatted": STRING,
    })),
    "verdict": enum("đạt", "cần sửa", "không đạt"),
})

# 10 --------------------------------------------------------------------
FACT_CHECK = obj({
    "checks": arr(obj({
        "id": STRING,
        "statement": STRING,
        "section_heading": STRING,
        "verdict": enum("đúng", "đúng một phần", "sai", "không kiểm chứng được"),
        "evidence": STRING,
        "source_ids": STR_LIST,
        "correction": STRING,
    })),
    "summary": obj({
        "total": INTEGER,
        "supported": INTEGER,
        "partial": INTEGER,
        "unsupported": INTEGER,
        "unverifiable": INTEGER,
    }),
    "blocking_issues": STR_LIST,
})

# 11 --------------------------------------------------------------------
PEER_REVIEW = obj({
    "scores": arr(obj({
        "dimension": STRING,
        "score": INTEGER,
        "comment": STRING,
    })),
    "strengths": STR_LIST,
    "required_revisions": arr(obj({
        "id": STRING,
        "section_heading": STRING,
        "problem": STRING,
        "action": STRING,
        "priority": enum("phải sửa", "nên sửa", "tuỳ chọn"),
    })),
    "decision": enum("chấp nhận", "chấp nhận sau chỉnh sửa nhỏ", "sửa lớn rồi xét lại"),
    "overall_comment": STRING,
})

# 12 --------------------------------------------------------------------
REVISION_LOG = obj({
    "applied": arr(obj({
        "ref_id": STRING,
        "what_changed": STRING,
        "section_heading": STRING,
    })),
    "skipped": arr(obj({
        "ref_id": STRING,
        "reason": STRING,
    })),
    "remaining_limitations": STR_LIST,
})
