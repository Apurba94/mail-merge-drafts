"""Templates use {{field}} placeholders with optional defaults {{field|default}}; first lines may set headers."""
import csv
import mimetypes
import os
import re
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

_PH = re.compile(r"\{\{\s*([\w .-]+?)\s*(?:\|\s*([^}]*?)\s*)?\}\}")
HEADERS = ("subject", "cc", "bcc", "reply-to", "from")


def parse_template(text):
    """Split 'Subject: ...' style header lines (until the first blank line) from the body."""
    headers, lines = {}, text.splitlines()
    i = 0
    while i < len(lines) and re.match(r"^([A-Za-z-]+):\s*(.*)$", lines[i]):
        k, v = re.match(r"^([A-Za-z-]+):\s*(.*)$", lines[i]).groups()
        if k.lower() not in HEADERS:
            break
        headers[k.lower()] = v
        i += 1
    if headers and i < len(lines) and not lines[i].strip():
        i += 1
    if "subject" not in headers:
        raise ValueError("template must start with a 'Subject:' line")
    return headers, "\n".join(lines[i:])


def placeholders(text):
    return sorted({m.group(1) for m in _PH.finditer(text)})


def render(text, row):
    """Fill placeholders; returns (text, missing_fields). Fields with defaults never count as missing."""
    missing = []

    def repl(m):
        key, default = m.group(1), m.group(2)
        val = (row.get(key) or "").strip()
        if val:
            return val
        if default is not None:
            return default
        missing.append(key)
        return "{{%s}}" % key
    return _PH.sub(repl, text), missing


def build_message(sender, to, headers, body, attachments=(), html=None):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = headers["subject"]
    for h in ("cc", "bcc", "reply-to"):
        if headers.get(h):
            msg[h.title() if h != "reply-to" else "Reply-To"] = headers[h]
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg["X-Unsent"] = "1"          # Outlook and others open .eml files with this header as editable drafts
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")
    for path in attachments:
        ctype, _ = mimetypes.guess_type(path)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        with open(path, "rb") as fh:
            msg.add_attachment(fh.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(path))
    return msg


def _safe(s):
    return re.sub(r"[^\w.-]+", "_", s)[:60] or "draft"


def make_drafts(rows, template, sender, outdir, email_col="email", attach_col="attachment", base_dir="."):
    """Write one .eml per row. Returns (written_paths, problems). Rows with problems are skipped."""
    headers, body = parse_template(template)
    os.makedirs(outdir, exist_ok=True)
    written, problems = [], []
    for i, row in enumerate(rows, start=2):
        to = (row.get(email_col) or "").strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", to):
            problems.append((i, "invalid or missing e-mail address %r" % to))
            continue
        hdrs = {}
        missing = []
        for k, v in headers.items():
            hdrs[k], miss = render(v, row)
            missing += miss
        text, miss = render(body, row)
        missing += miss
        if missing:
            problems.append((i, "%s: missing value(s) for %s" % (to, ", ".join(sorted(set(missing))))))
            continue
        atts = []
        for a in re.split(r"[;|]", row.get(attach_col) or ""):
            a = a.strip()
            if a:
                p = a if os.path.isabs(a) else os.path.join(base_dir, a)
                if not os.path.exists(p):
                    problems.append((i, "%s: attachment not found: %s" % (to, a)))
                    atts = None
                    break
                atts.append(p)
        if atts is None:
            continue
        msg = build_message(sender, to, hdrs, text, atts)
        path = os.path.join(outdir, "%03d_%s.eml" % (len(written) + 1, _safe(to)))
        with open(path, "wb") as fh:
            fh.write(bytes(msg))
        written.append(path)
    return written, problems


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))
