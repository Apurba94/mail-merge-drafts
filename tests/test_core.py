import email
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from mail_merge_drafts.cli import main
from mail_merge_drafts.core import make_drafts, parse_template, placeholders, render

TEMPLATE = """Subject: Invitation to review: {{paper}}
Cc: {{cc|}}

Dear {{title|Dr.}} {{last_name}},

Would you review "{{paper}}" by {{deadline}}?

Best regards,
Ana
"""


class TemplateTests(unittest.TestCase):
    def test_parse_and_placeholders(self):
        h, body = parse_template(TEMPLATE)
        self.assertEqual(h["subject"], "Invitation to review: {{paper}}")
        self.assertTrue(body.startswith("Dear"))
        self.assertEqual(placeholders(TEMPLATE), ["cc", "deadline", "last_name", "paper", "title"])
        with self.assertRaises(ValueError):
            parse_template("Hello {{name}}")

    def test_render_defaults_and_missing(self):
        text, missing = render("Dear {{title|Dr.}} {{last_name}} {{x}}", {"last_name": "Curie", "title": ""})
        self.assertEqual(text, "Dear Dr. Curie {{x}}")
        self.assertEqual(missing, ["x"])


class DraftTests(unittest.TestCase):
    def test_make_drafts(self):
        rows = [{"email": "marie@uni.fr", "last_name": "Curie", "paper": "Radium", "deadline": "1 May", "attachment": "a.pdf"},
                {"email": "not-an-email", "last_name": "X", "paper": "P", "deadline": "d"},
                {"email": "bo@x.org", "last_name": "", "paper": "P", "deadline": "d"}]
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "a.pdf"), "wb") as fh:
                fh.write(b"%PDF-1.4")
            written, problems = make_drafts(rows, TEMPLATE, "ana@lab.org", os.path.join(d, "out"), base_dir=d)
            self.assertEqual(len(written), 1)
            self.assertEqual([p[0] for p in problems], [3, 4])
            with open(written[0], "rb") as fh:
                msg = email.message_from_bytes(fh.read())
            self.assertEqual(msg["Subject"], "Invitation to review: Radium")
            self.assertEqual(msg["X-Unsent"], "1")
            self.assertIsNone(msg["Cc"])
            parts = list(msg.walk())
            self.assertIn("Dear Dr. Curie", parts[1].get_payload(decode=True).decode())
            self.assertEqual(parts[-1].get_filename(), "a.pdf")

    def test_missing_attachment(self):
        with tempfile.TemporaryDirectory() as d:
            row = {"email": "a@b.org", "last_name": "A", "paper": "P", "deadline": "d", "attachment": "nope.pdf"}
            written, problems = make_drafts([row], TEMPLATE, "me@x.org", d, base_dir=d)
            self.assertEqual(written, [])
            self.assertIn("attachment not found", problems[0][1])

    def test_cli_preview_and_write(self):
        with tempfile.TemporaryDirectory() as d:
            csvp, tp = os.path.join(d, "r.csv"), os.path.join(d, "t.txt")
            with open(csvp, "w", encoding="utf-8") as fh:
                fh.write("email,last_name,paper,deadline\nmarie@uni.fr,Curie,Radium,1 May\n")
            with open(tp, "w", encoding="utf-8") as fh:
                fh.write(TEMPLATE)
            with redirect_stdout(io.StringIO()) as buf, redirect_stderr(io.StringIO()):
                main([csvp, tp, "--from", "ana@lab.org", "--preview", "1"])
                self.assertEqual(main([csvp, tp, "--from", "ana@lab.org", "-o", os.path.join(d, "drafts")]), 0)
            self.assertIn("Subject: Invitation to review: Radium", buf.getvalue())
            self.assertEqual(len(os.listdir(os.path.join(d, "drafts"))), 1)


if __name__ == "__main__":
    unittest.main()
