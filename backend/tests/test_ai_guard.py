import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.services import ai_guard as g
CTX = '{"company_name":"Acme","employee_count":120,"annual_revenue":20000000,"email":"x@acme.io","score":73}'

class T(unittest.TestCase):
    def test_supported_numbers_pass(self):
        self.assertEqual(g.find_unsupported("Acme has 120 employees and scored 73; revenue 20,000,000.", CTX), [])
        self.assertEqual(g.find_unsupported("Revenue is about 20 million", CTX), [])
    def test_invented_numbers_flagged(self):
        self.assertEqual(g.find_unsupported("They grew 45% last year", CTX), ["45"])
    def test_duration_and_enumerators_exempt(self):
        self.assertEqual(g.find_unsupported("1. Call\n2. Email\nHave a 15 minute chat?", CTX), [])
    def test_invented_email_and_url(self):
        self.assertEqual(g.find_unsupported("mail y@evil.io", CTX), ["y@evil.io"])
        self.assertEqual(g.find_unsupported("see https://made-up.com/x", CTX), ["https://made-up.com/x"])
        self.assertEqual(g.find_unsupported("reach x@acme.io", CTX), [])
    def test_forbidden_phrases(self):
        self.assertIn("i noticed", g.find_forbidden_phrases("I noticed your growth"))
        self.assertIn("we spoke", g.find_forbidden_phrases("As WE SPOKE earlier"))
        self.assertEqual(g.find_forbidden_phrases("Hello, I would like to introduce myself."), [])
    def test_extract_json(self):
        self.assertEqual(g.extract_json('{"a":1}'), {"a": 1})
        self.assertEqual(g.extract_json('```json\n{"a":1}\n```'), {"a": 1})
        self.assertEqual(g.extract_json('Sure! {"a":1} done'), {"a": 1})
        with self.assertRaises(ValueError): g.extract_json("no json")
        with self.assertRaises(ValueError): g.extract_json(None)

if __name__ == "__main__": unittest.main()
