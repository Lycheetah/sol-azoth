"""P2-T3: Memory summarizer tests."""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

def test_summarizer_importable():
    from CORE.memory_summarizer import summarize, maybe_summarize, recall_summaries, status
    return True, "summarize + maybe_summarize + recall_summaries + status importable"

def test_no_compress_under_threshold():
    from CORE.memory_engine import MemoryEngine
    from CORE.memory_summarizer import summarize
    with tempfile.TemporaryDirectory() as d:
        eng = MemoryEngine(db_path=os.path.join(d, "test.db"))
        for i in range(20):
            eng.store_episode(f"action_{i}", result=f"result_{i}")
        result = summarize(eng, threshold=100)
        assert not result["compressed"], f"Should not compress under threshold: {result}"
        assert result["before"] == 20
    return True, "no compression when count < threshold"

def test_compress_over_threshold():
    from CORE.memory_engine import MemoryEngine
    from CORE.memory_summarizer import summarize, episode_count
    with tempfile.TemporaryDirectory() as d:
        eng = MemoryEngine(db_path=os.path.join(d, "test.db"))
        for i in range(110):
            eng.store_episode(f"action_{i%10}", result=f"result_{i}", success=(i%5 != 0))
        result = summarize(eng, threshold=100, batch_size=50)
        assert result["compressed"], f"Should compress over threshold: {result}"
        assert result["batch"] == 50, f"Expected 50 compressed, got {result['batch']}"
        assert result["after"] == 60, f"Expected 60 remaining, got {result['after']}"
        assert result["summary_id"] is not None
    return True, f"compressed 50 episodes, {result['after']} remain"

def test_summary_stored_as_learning():
    from CORE.memory_engine import MemoryEngine
    from CORE.memory_summarizer import summarize, recall_summaries
    with tempfile.TemporaryDirectory() as d:
        eng = MemoryEngine(db_path=os.path.join(d, "test.db"))
        for i in range(110):
            eng.store_episode(f"act_{i}", result="ok")
        summarize(eng, threshold=100, batch_size=50)
        sums = recall_summaries(eng)
        assert len(sums) >= 1, f"No summaries found: {sums}"
        assert "COMPRESSED EPISODE BATCH" in sums[0]["insight"]
    return True, f"summary stored as learning, insight contains batch header"

def test_summary_content_quality():
    from CORE.memory_engine import MemoryEngine
    from CORE.memory_summarizer import summarize, recall_summaries
    with tempfile.TemporaryDirectory() as d:
        eng = MemoryEngine(db_path=os.path.join(d, "test.db"))
        for i in range(110):
            eng.store_episode(f"forge_run_{i%3}", result="built", success=True)
        for i in range(5):
            eng.store_episode("compile_check", result="FAIL: syntax error", success=False)
        summarize(eng, threshold=100, batch_size=50)
        sums = recall_summaries(eng)
        insight = sums[0]["insight"]
        assert "Top actions" in insight, f"Missing Top actions in insight"
        assert "Failures" in insight, f"Missing Failures in insight"
    return True, "summary insight contains actions + failure info"

def test_status_report():
    from CORE.memory_engine import MemoryEngine
    from CORE.memory_summarizer import status
    with tempfile.TemporaryDirectory() as d:
        eng = MemoryEngine(db_path=os.path.join(d, "test.db"))
        for i in range(50):
            eng.store_episode(f"act_{i}", result="ok")
        s = status(eng)
        assert s["episodes_live"] == 50
        assert not s["needs_compress"]
        assert "threshold" in s
    return True, f"status(): episodes={s['episodes_live']}, needs_compress={s['needs_compress']}"

def test_double_compress():
    """Running summarize twice should compress again if still over threshold."""
    from CORE.memory_engine import MemoryEngine
    from CORE.memory_summarizer import summarize, recall_summaries, episode_count
    with tempfile.TemporaryDirectory() as d:
        eng = MemoryEngine(db_path=os.path.join(d, "test.db"))
        for i in range(160):
            eng.store_episode(f"act_{i}", result="ok")
        summarize(eng, threshold=100, batch_size=50)   # 160 → 110
        summarize(eng, threshold=100, batch_size=50)   # 110 → 60
        sums = recall_summaries(eng, limit=10)
        assert len(sums) == 2, f"Expected 2 summaries, got {len(sums)}"
        assert episode_count(eng) == 60
    return True, "double compress: 160 → 110 → 60 episodes, 2 summaries"
