import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.services import csv_parser as p

GOOD = b"Company,Email,Employees,Revenue\nAcme,A@X.COM,\"1,200\",$5000000\nBeta,,50,\n"

class T(unittest.TestCase):
    def test_alias_mapping_and_cleaning(self):
        r = p.parse_csv(GOOD)
        rows = p.classify(r["rows"], set())
        self.assertEqual(rows[0]["data"]["email"], "a@x.com")
        self.assertEqual(rows[0]["data"]["employee_count"], 1200)
        self.assertEqual(rows[0]["data"]["annual_revenue"], 5000000)
        self.assertEqual([x["status"] for x in rows], ["valid", "valid"])
    def test_empty_and_header_only(self):
        for b in (b"", b"  \n"):
            with self.assertRaises(p.CsvFileError): p.parse_csv(b)
        with self.assertRaises(p.CsvFileError): p.parse_csv(b"company_name,email\n")
    def test_missing_required_column(self):
        with self.assertRaises(p.CsvFileError) as c: p.parse_csv(b"email,industry\na@b.co,X\n")
        self.assertIn("company_name", str(c.exception))
    def test_binary_and_encoding(self):
        with self.assertRaises(p.CsvFileError): p.parse_csv(b"\x00\x01\x02")
        with self.assertRaises(p.CsvFileError): p.parse_csv("company_name\nCaf\xe9".encode("latin-1"))
    def test_row_errors(self):
        r = p.parse_csv(b"company_name,email,employee_count\n,bad,abc\nOk,ok@ok.io,5\n")
        rows = p.classify(r["rows"], set())
        self.assertEqual(rows[0]["status"], "invalid"); self.assertEqual(len(rows[0]["errors"]), 3)
        self.assertEqual(rows[1]["status"], "valid")
    def test_duplicates_file_and_db(self):
        r = p.parse_csv(b"company_name,email\nA,a@a.io\na,A@a.io\nB,\n")
        rows = p.classify(r["rows"], {p.dedupe_key("B", None)})
        self.assertEqual([(x["status"], x["duplicate_of"]) for x in rows],
                         [("valid", None), ("duplicate", "file"), ("duplicate", "database")])
    def test_corrections_fix_invalid_row(self):
        r = p.parse_csv(b"company_name,email\nA,nope\n")
        p.apply_corrections(r["rows"], {str(r["rows"][0]["row_number"]): {"email": "a@a.io", "bogus": "x"}})
        self.assertEqual(p.classify(r["rows"], set())[0]["status"], "valid")
    def test_row_limit_and_explicit_mapping(self):
        with self.assertRaises(p.CsvFileError): p.parse_csv(b"company_name\nA\nB\n", max_rows=1)
        r = p.parse_csv(b"Org,Foo\nZed,1\n", mapping={"Org": "company_name", "Foo": ""})
        self.assertEqual(r["rows"][0]["raw"]["company_name"], "Zed")
        with self.assertRaises(p.CsvFileError): p.parse_csv(b"A,B\n1,2\n", mapping={"A": "nope"})
    def test_extra_cells_flagged(self):
        r = p.parse_csv(b"company_name,email\nA,a@a.io,extra\n")
        self.assertEqual(p.classify(r["rows"], set())[0]["status"], "invalid")
    def test_sample_file_parses(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "sample_leads.csv")
        rows = p.classify(p.parse_csv(open(path, "rb").read())["rows"], set())
        self.assertEqual(len(rows), 20); self.assertTrue(all(x["status"] == "valid" for x in rows))
    def test_formula_injection(self):
        self.assertEqual(p.csv_safe("=1+1"), "'=1+1"); self.assertEqual(p.csv_safe("@x"), "'@x")
        self.assertEqual(p.csv_safe("ok"), "ok"); self.assertEqual(p.csv_safe(None), "")

if __name__ == "__main__": unittest.main()
