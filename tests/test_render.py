from datetime import datetime
from src import html_renderer, email_renderer, vitals

D = datetime(2026, 6, 6)
STORIES = [{"writer_key": "sports", "spread_type": "hero", "topic_label": "THE BENCH",
            "headline": "Headline Here", "deck": "Deck.", "body": "Para one.\n\nPara two.",
            "pull_quote": "A quote.", "stat": "", "source": "Src", "recurring_bit_content": "THE LEDE"}]

def _vit():
    return vitals.build_vitals({}, None, D)

def test_web_render_smoke():
    out = html_renderer.render_issue(D, STORIES, issue={"masthead_label": "X"}, vitals=_vit())
    assert "Pulse" in out and 'class="vitals"' in out
    assert out.lstrip().startswith("<!doctype html") and out.rstrip().endswith("</html>")

def test_render_vitals_empty_is_blank():
    assert html_renderer.render_vitals(None) == ""
    assert html_renderer.render_vitals({"cells": []}) == ""

def test_email_render_is_inbox_safe():
    em = email_renderer.render_email_issue(D, STORIES, issue={"masthead_label": "X"},
                                           vitals=_vit(), web_url="https://example.com/i.html")
    assert "<table" in em
    assert "display:flex" not in em and "display:grid" not in em
    assert "clamp(" not in em                      # no responsive CSS funcs in email
    assert "THE VITALS" in em
    assert "https://example.com/i.html" in em      # gateway link wired
