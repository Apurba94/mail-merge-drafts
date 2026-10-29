"""Create personalized e-mail drafts (.eml) from a CSV and a template, without sending anything."""
from .core import parse_template, placeholders, render, build_message, make_drafts

__version__ = "0.1.0"
__all__ = ["parse_template", "placeholders", "render", "build_message", "make_drafts"]
