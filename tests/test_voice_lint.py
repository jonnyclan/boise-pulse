from src import voice_lint

def _lifestyle(body, rbc):
    return {"writer_key": "lifestyle", "spread_type": "rose_stamp", "topic_label": "SATURDAY TRIED IT",
            "headline": "h", "deck": "d", "pull_quote": "p", "stat": "", "source": "src",
            "body": body, "recurring_bit_content": rbc}

def _fails(findings):
    return [f for f in findings if f[0] == "FAIL"]

def test_clean_lifestyle_has_no_fail():
    good = _lifestyle("I tried it Saturday at the Meridian Target.\n\nIt held up fine.",
                      "HAYLEY'S RATIO: $34 / 90 minutes / 2/2 kids intact. TRIED IT.")
    assert _fails(voice_lint.lint([good], ["rose_stamp"])) == []

def test_banned_word_and_missing_ratio_fail():
    bad = _lifestyle("This is amazing, babe.\n\nLoved it.", "no ratio here")
    msgs = " ".join(f[3] for f in _fails(voice_lint.lint([bad], ["rose_stamp"])))
    assert "babe" in msgs
    assert "HAYLEY'S RATIO" in msgs
    assert "verdict" in msgs.lower()

def test_duplicate_writer_is_hard_fail():
    s = {"writer_key": "sports", "spread_type": "broadsheet", "topic_label": "THE BENCH",
         "headline": "h", "deck": "d", "pull_quote": "q", "stat": "37", "source": "src",
         "body": "The Blue looked sharp.\n\nBroncos rolled.", "recurring_bit_content": "THE LEDE"}
    s2 = dict(s); s2["spread_type"] = "hero"
    msgs = " ".join(f[3] for f in _fails(voice_lint.lint([s, s2], ["broadsheet", "hero"])))
    assert "sports" in msgs and "2x" in msgs

def test_spread_count_mismatch_fails():
    s = {"writer_key": "sports", "spread_type": "hero", "headline": "h", "body": "x", "source": "src"}
    assert _fails(voice_lint.lint([s], ["hero", "broadsheet"]))  # 1 story vs 2 planned
