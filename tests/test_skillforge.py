"""H1 SKILL FORGE — regression tests. Isolated skills dir per test."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from CORE import skillforge as SF


@pytest.fixture(autouse=True)
def _isolate_skills(tmp_path, monkeypatch):
    monkeypatch.setattr(SF, "SKILLS_DIR", tmp_path / "SKILLS")


def test_save_and_file_shape():
    out = SF.save_skill("Fix a poisoned tool history",
                        "When gated done calls start 400-looping",
                        "1. Find the double tool message\n2. REPLACE, never append")
    assert "forged" in out
    p = SF.SKILLS_DIR / "fix-a-poisoned-tool-history.md"
    assert p.exists()
    text = p.read_text()
    assert "## WHEN TO USE" in text and "uses: 0" in text


def test_save_validates():
    assert "ERROR" in SF.save_skill("", "when", "steps")
    assert "ERROR" in SF.save_skill("name", "when", "  ")


def test_refine_preserves_history():
    SF.save_skill("Deploy thing", "when deploying", "step one")
    out = SF.save_skill("Deploy thing", "when deploying v2", "better step")
    assert "refined" in out
    text = (SF.SKILLS_DIR / "deploy-thing.md").read_text()
    assert "step one" in text and "## REFINED" in text and "better step" in text


def test_recall_matches_and_bumps_uses():
    SF.save_skill("Fix expo metro cache", "When expo shows stale bundle errors",
                  "npx expo start -c")
    out = SF.recall_skills("expo bundle stale")
    assert "npx expo start -c" in out
    assert "uses: 1" in (SF.SKILLS_DIR / "fix-expo-metro-cache.md").read_text()


def test_recall_no_match_is_honest():
    SF.save_skill("A thing", "for a-things only", "do it")
    assert "No skill matches" in SF.recall_skills("quantum entanglement")


def test_index_block_lists_skills():
    SF.save_skill("First skill", "situation one", "steps")
    SF.save_skill("Second skill", "situation two", "steps")
    idx = SF.index_block()
    assert "First skill" in idx and "Second skill" in idx and "FORGED SKILLS" in idx


def test_index_empty_when_no_skills():
    assert SF.index_block() == ""


def test_agent_tools_dispatch():
    import agent as A
    out = A.dispatch_tool("skill_save", {"name": "Test skill", "when_to_use": "x", "steps": "y"})
    assert "forged" in out
    out = A.dispatch_tool("skill_recall", {"query": "test skill"})
    assert "Test skill" in out
    assert "ERROR" in A.dispatch_tool("skill_recall", {})
