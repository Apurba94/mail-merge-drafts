"""Command-line interface for mail-merge-drafts."""
import argparse
import os
import sys

from .core import make_drafts, parse_template, placeholders, read_rows, render


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mail-merge-drafts",
                                 description="Personalized e-mail DRAFTS (.eml) from a CSV and a template. Nothing is sent.")
    ap.add_argument("csvfile", help="recipients with an 'email' column and template fields")
    ap.add_argument("template", help="text template: 'Subject: ...' line, blank line, body with {{field}}")
    ap.add_argument("--from", dest="sender", required=True, help="your address")
    ap.add_argument("-o", "--outdir", default="drafts")
    ap.add_argument("--email-col", default="email")
    ap.add_argument("--attach-col", default="attachment", help="column with file path(s), separated by ';'")
    ap.add_argument("--preview", type=int, metavar="N", help="print the first N rendered messages instead of writing")
    args = ap.parse_args(argv)
    rows = read_rows(args.csvfile)
    with open(args.template, encoding="utf-8") as fh:
        template = fh.read()
    headers, body = parse_template(template)
    cols = set(rows[0]) if rows else set()
    unknown = [p for p in placeholders(template) if p not in cols]
    if unknown:
        print("warning: template fields not in CSV: %s" % ", ".join(unknown), file=sys.stderr)
    if args.preview:
        for row in rows[:args.preview]:
            subj, _ = render(headers["subject"], row)
            text, miss = render(body, row)
            print("To: %s\nSubject: %s\n\n%s\n%s" % (row.get(args.email_col), subj, text, "-" * 60))
        return 0
    written, problems = make_drafts(rows, template, args.sender, args.outdir, args.email_col, args.attach_col,
                                    os.path.dirname(os.path.abspath(args.csvfile)))
    for line, msg in problems:
        print("row %d skipped: %s" % (line, msg), file=sys.stderr)
    print("%d draft(s) written to %s (open them in your mail client to review and send)" % (len(written), args.outdir))
    return 1 if problems else 0
