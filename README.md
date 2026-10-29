# mail-merge-drafts

**Write one template, get personalized e-mail drafts for every collaborator, reviewer or
participant, as `.eml` files you review and send yourself. Nothing is ever sent automatically.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Inviting reviewers, contacting study sites, sending participants their personal results, chasing
co-author contributions: research involves many near-identical e-mails. Copy-pasting names invites
embarrassing mistakes ("Dear {Name}", the wrong attachment). Mail-merge features in office suites are
clumsy and fully automatic senders are risky. Drafts give you automation and a final human check.

## Features

- Template with `Subject:`/`Cc:`/`Bcc:`/`Reply-To:` header lines and `{{field}}` placeholders, defaults with `{{field|default}}`
- One `.eml` per CSV row with the `X-Unsent: 1` header, so mail clients (e.g. Outlook) open it as an editable draft
- Per-row attachments (`attachment` column, several separated by `;`)
- Validation: invalid addresses, missing values and missing attachments skip the row and are reported
- `--preview N` prints rendered messages first; warns about template fields absent from the CSV

## Usage

```bash
pip install .
mail-merge-drafts reviewers.csv invite_template.txt --from you@university.edu --preview 2
mail-merge-drafts reviewers.csv invite_template.txt --from you@university.edu -o drafts/
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
