"""Deterministic, rule-based lead scoring. Pure Python, no I/O, no AI.

The LLM never touches the score. Identical lead + ICP => identical result.
Missing data is excluded from the score (not treated as a mismatch); if too
little evaluable data exists the lead gets REVIEW_REQUIRED instead of a verdict.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

STRONG, POTENTIAL, WEAK = "strong_match", "potential_match", "weak_match"
EXCLUDED, REVIEW = "excluded", "review_required"


@dataclass
class ICP:
    target_industries: list[str] = field(default_factory=list)
    excluded_industries: list[str] = field(default_factory=list)
    min_employees: int | None = None
    max_employees: int | None = None
    target_locations: list[str] = field(default_factory=list)
    min_revenue: float | None = None
    max_revenue: float | None = None
    keywords: list[str] = field(default_factory=list)
    excluded_keywords: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=lambda: {
        "industry": 30, "company_size": 25, "location": 15, "revenue": 10, "keywords": 20})
    strong_threshold: int = 80
    potential_threshold: int = 60
    min_evaluable_weight_pct: float = 50.0  # below this => review required

    def validate(self) -> None:
        if any(w < 0 for w in self.weights.values()):
            raise ValueError("weights must be non-negative")
        if sum(self.weights.values()) <= 0:
            raise ValueError("at least one weight must be positive")
        if not 0 <= self.potential_threshold <= self.strong_threshold <= 100:
            raise ValueError("thresholds must satisfy 0 <= potential <= strong <= 100")
        if None not in (self.min_employees, self.max_employees) and self.min_employees > self.max_employees:
            raise ValueError("min_employees > max_employees")
        if None not in (self.min_revenue, self.max_revenue) and self.min_revenue > self.max_revenue:
            raise ValueError("min_revenue > max_revenue")


@dataclass
class Factor:
    name: str
    status: str            # match | partial | mismatch | missing
    earned: float
    max_points: float
    detail: str


@dataclass
class ScoreResult:
    score: int
    category: str
    factors: list[Factor]
    evaluable_weight_pct: float
    exclusion_reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"score": self.score, "category": self.category,
                "evaluable_weight_pct": self.evaluable_weight_pct,
                "exclusion_reasons": self.exclusion_reasons,
                "factors": [vars(f) for f in self.factors]}


def _norm(s: Any) -> str:
    return str(s).strip().lower() if s is not None else ""


def _blank(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def _in_range(v: float, lo, hi) -> bool:
    return (lo is None or v >= lo) and (hi is None or v <= hi)


def _closeness(v: float, lo, hi) -> bool:
    """Within 25% outside the range counts as a partial match."""
    lo2 = lo * 0.75 if lo is not None else None
    hi2 = hi * 1.25 if hi is not None else None
    return _in_range(v, lo2, hi2)


def score_lead(lead: dict[str, Any], icp: ICP) -> ScoreResult:
    icp.validate()
    w = icp.weights
    factors: list[Factor] = []
    text = " ".join(_norm(lead.get(k)) for k in ("description", "company_name", "industry"))

    exclusions: list[str] = []
    ind = _norm(lead.get("industry"))
    if ind and ind in {_norm(x) for x in icp.excluded_industries}:
        exclusions.append(f"Industry '{lead.get('industry')}' is excluded by the ICP")
    for kw in icp.excluded_keywords:
        if _norm(kw) and _norm(kw) in text:
            exclusions.append(f"Excluded characteristic '{kw}' found in lead data")

    wt = w.get("industry", 0)
    if _blank(lead.get("industry")) or not icp.target_industries:
        factors.append(Factor("industry", "missing", 0, wt, "Industry not provided" if _blank(lead.get("industry")) else "ICP has no target industries"))
    elif ind in {_norm(x) for x in icp.target_industries}:
        factors.append(Factor("industry", "match", wt, wt, f"Industry '{lead['industry']}' is a target industry"))
    else:
        factors.append(Factor("industry", "mismatch", 0, wt, f"Industry '{lead['industry']}' is not a target industry"))

    wt = w.get("company_size", 0)
    emp = lead.get("employee_count")
    if emp is None or (icp.min_employees is None and icp.max_employees is None):
        factors.append(Factor("company_size", "missing", 0, wt, "Employee count not provided" if emp is None else "ICP has no size range"))
    elif _in_range(emp, icp.min_employees, icp.max_employees):
        factors.append(Factor("company_size", "match", wt, wt, f"{emp} employees is within the target range"))
    elif _closeness(emp, icp.min_employees, icp.max_employees):
        factors.append(Factor("company_size", "partial", wt * 0.5, wt, f"{emp} employees is close to the target range"))
    else:
        factors.append(Factor("company_size", "mismatch", 0, wt, f"{emp} employees is outside the target range"))

    wt = w.get("location", 0)
    loc = _norm(lead.get("location"))
    if not loc or not icp.target_locations:
        factors.append(Factor("location", "missing", 0, wt, "Location not provided" if not loc else "ICP has no target locations"))
    elif any(_norm(t) and (_norm(t) in loc or loc in _norm(t)) for t in icp.target_locations):
        factors.append(Factor("location", "match", wt, wt, f"Location '{lead['location']}' matches a target location"))
    else:
        factors.append(Factor("location", "mismatch", 0, wt, f"Location '{lead['location']}' is not a target location"))

    wt = w.get("revenue", 0)
    rev = lead.get("annual_revenue")
    if rev is None or (icp.min_revenue is None and icp.max_revenue is None):
        factors.append(Factor("revenue", "missing", 0, wt, "Revenue not provided" if rev is None else "ICP has no revenue range"))
    elif _in_range(rev, icp.min_revenue, icp.max_revenue):
        factors.append(Factor("revenue", "match", wt, wt, "Revenue is within the target range"))
    elif _closeness(rev, icp.min_revenue, icp.max_revenue):
        factors.append(Factor("revenue", "partial", wt * 0.5, wt, "Revenue is close to the target range"))
    else:
        factors.append(Factor("revenue", "mismatch", 0, wt, "Revenue is outside the target range"))

    wt = w.get("keywords", 0)
    desc = _norm(lead.get("description"))
    kws = [k for k in icp.keywords if _norm(k)]
    if not desc or not kws:
        factors.append(Factor("keywords", "missing", 0, wt, "Business description not provided" if not desc else "ICP has no keywords"))
    else:
        hits = [k for k in kws if _norm(k) in desc]
        frac = len(hits) / len(kws)
        status = "match" if frac >= 0.5 else ("partial" if hits else "mismatch")
        detail = f"Matched {len(hits)}/{len(kws)} keywords" + (f": {', '.join(hits)}" if hits else "")
        factors.append(Factor("keywords", status, round(wt * frac, 2), wt, detail))

    evaluable = [f for f in factors if f.status != "missing" and f.max_points > 0]
    total_w = sum(f.max_points for f in factors) or 1.0
    eval_w = sum(f.max_points for f in evaluable)
    eval_pct = round(eval_w / total_w * 100, 1)
    score = round(sum(f.earned for f in evaluable) / eval_w * 100) if eval_w else 0

    if exclusions:
        category = EXCLUDED
    elif eval_pct < icp.min_evaluable_weight_pct:
        category = REVIEW
    elif score >= icp.strong_threshold:
        category = STRONG
    elif score >= icp.potential_threshold:
        category = POTENTIAL
    else:
        category = WEAK
    return ScoreResult(score, category, factors, eval_pct, exclusions)
