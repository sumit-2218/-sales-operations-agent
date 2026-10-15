import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.services.lead_scoring_service import ICP, score_lead, STRONG, WEAK, EXCLUDED, REVIEW, POTENTIAL

ICP_ = ICP(target_industries=["Software", "Logistics"], excluded_industries=["Gambling"],
           min_employees=50, max_employees=500, target_locations=["Germany", "Austria"],
           min_revenue=5e6, max_revenue=100e6, keywords=["saas", "automation", "b2b"],
           excluded_keywords=["nonprofit"])
FULL = dict(company_name="Acme", industry="Software", employee_count=120, location="Berlin, Germany",
            annual_revenue=20e6, description="B2B SaaS automation platform")

class T(unittest.TestCase):
    def test_strong(self):
        r = score_lead(FULL, ICP_); self.assertEqual((r.score, r.category), (100, STRONG))
    def test_reproducible(self):
        self.assertEqual(score_lead(FULL, ICP_).to_dict(), score_lead(dict(FULL), ICP_).to_dict())
    def test_weak(self):
        l = dict(FULL, industry="Retail", employee_count=5, location="Brazil", annual_revenue=1e5, description="shop")
        r = score_lead(l, ICP_); self.assertEqual(r.category, WEAK); self.assertLess(r.score, 60)
    def test_excluded_industry_overrides_high_score(self):
        r = score_lead(dict(FULL, industry="Gambling"), ICP_)
        self.assertEqual(r.category, EXCLUDED); self.assertTrue(r.exclusion_reasons)
    def test_excluded_keyword(self):
        r = score_lead(dict(FULL, description="Nonprofit B2B SaaS"), ICP_); self.assertEqual(r.category, EXCLUDED)
    def test_missing_is_not_mismatch(self):
        l = dict(FULL); l.update(annual_revenue=None, description=None)
        r = score_lead(l, ICP_)
        self.assertEqual({f.name: f.status for f in r.factors}["revenue"], "missing")
        self.assertEqual(r.score, 100); self.assertEqual(r.category, STRONG)
    def test_insufficient_data_requires_review(self):
        r = score_lead({"company_name": "Mystery", "industry": "Software"}, ICP_); self.assertEqual(r.category, REVIEW)
    def test_partial_size(self):
        r = score_lead(dict(FULL, employee_count=40), ICP_)
        self.assertEqual({f.name: f.status for f in r.factors}["company_size"], "partial")
    def test_potential_band(self):
        l = dict(FULL, location="France", description="B2B platform")
        r = score_lead(l, ICP_); self.assertEqual(r.category, POTENTIAL, r.score)
    def test_validation(self):
        with self.assertRaises(ValueError): score_lead(FULL, ICP(weights={"industry": -1}))
        with self.assertRaises(ValueError): score_lead(FULL, ICP(min_employees=10, max_employees=1))
        with self.assertRaises(ValueError): score_lead(FULL, ICP(strong_threshold=50, potential_threshold=60))

if __name__ == "__main__": unittest.main()
