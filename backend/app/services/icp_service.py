"""ICP helpers: defaults, conversion to the scoring dataclass, human-readable explanations."""
from dataclasses import fields

from .lead_scoring_service import ICP

DEFAULT_ICP_CONFIG = {
    "target_industries": ["Software", "Logistics", "Fintech", "Manufacturing"],
    "excluded_industries": ["Gambling"],
    "min_employees": 50, "max_employees": 500,
    "target_locations": ["Germany", "Austria"],
    "min_revenue": 5_000_000, "max_revenue": 100_000_000,
    "keywords": ["saas", "automation", "b2b", "analytics"],
    "excluded_keywords": ["nonprofit"],
    "weights": {"industry": 30, "company_size": 25, "location": 15, "revenue": 10, "keywords": 20},
    "strong_threshold": 80, "potential_threshold": 60, "min_evaluable_weight_pct": 50.0,
}


def to_icp(config: dict) -> ICP:
    names = {f.name for f in fields(ICP)}
    return ICP(**{k: v for k, v in config.items() if k in names})


def explain_icp(c: dict) -> list[str]:
    w = c.get("weights", {})
    tot = sum(w.values()) or 1
    pct = lambda k: round(w.get(k, 0) / tot * 100)
    out = []
    if c.get("target_industries"):
        out.append(f"Industry ({pct('industry')}% of the score): full points if the lead's industry is one of "
                   f"{', '.join(c['target_industries'])}; none otherwise. Missing industry is not penalised.")
    if c.get("min_employees") is not None or c.get("max_employees") is not None:
        out.append(f"Company size ({pct('company_size')}%): full points within {c.get('min_employees')}–"
                   f"{c.get('max_employees')} employees, half points within 25% outside that range.")
    if c.get("target_locations"):
        out.append(f"Location ({pct('location')}%): full points if the location contains one of "
                   f"{', '.join(c['target_locations'])}.")
    if c.get("min_revenue") is not None or c.get("max_revenue") is not None:
        out.append(f"Revenue ({pct('revenue')}%): full points within {c.get('min_revenue')}–{c.get('max_revenue')}, "
                   "half points within 25% outside; ignored when revenue is unknown.")
    if c.get("keywords"):
        out.append(f"Keywords ({pct('keywords')}%): points proportional to how many of "
                   f"{', '.join(c['keywords'])} appear in the business description.")
    if c.get("excluded_industries") or c.get("excluded_keywords"):
        out.append("Exclusions: leads in an excluded industry or whose data contains an excluded keyword are "
                   "marked 'excluded' regardless of their numeric score.")
    out.append(f"Categories: {c.get('strong_threshold')}+ strong match, {c.get('potential_threshold')}–"
               f"{(c.get('strong_threshold') or 1) - 1} potential match, below that weak match. Criteria with missing lead data "
               f"are left out of the score; if less than {c.get('min_evaluable_weight_pct')}% of the weight can be "
               "evaluated the lead is marked 'review required'.")
    return out
