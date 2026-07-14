"""P1-T1: SQLite memory engine tests."""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

def test_memory_engine_importable():
    from CORE.memory_engine import MemoryEngine
    return True, "MemoryEngine class importable"

def test_memory_episode_store_recall():
    from CORE.memory_engine import MemoryEngine
    with tempfile.TemporaryDirectory() as d:
        eng = MemoryEngine(db_path=os.path.join(d, "test.db"))
        eng.store_episode("test_action", context="ctx", result="ok", tags=["test"])
        eps = eng.recent_episodes(limit=5)
        assert len(eps) >= 1, f"Expected >=1 episode, got {len(eps)}"
        assert any("test_action" in str(e) for e in eps), f"Action not found in episodes: {eps}"
    return True, "store_episode + recent_episodes roundtrip"

def test_memory_learn_recall():
    from CORE.memory_engine import MemoryEngine
    with tempfile.TemporaryDirectory() as d:
        eng = MemoryEngine(db_path=os.path.join(d, "test.db"))
        eng.learn("test_topic", "test insight about π", confidence=0.9)
        learnings = eng.recall_learnings(topic="test_topic")
        assert len(learnings) >= 1, f"Expected learnings, got {len(learnings)}"
    return True, "learn + recall_learnings roundtrip"

def test_memory_capability_register():
    from CORE.memory_engine import MemoryEngine
    with tempfile.TemporaryDirectory() as d:
        eng = MemoryEngine(db_path=os.path.join(d, "test.db"))
        eng.register_capability("test_cap", level="3", description="test capability")
        caps = eng.list_capabilities()
        names = [c.get("name") for c in caps]
        assert "test_cap" in names, f"test_cap not in {names}"
    return True, "register_capability + list_capabilities"

def test_memory_task_lifecycle():
    from CORE.memory_engine import MemoryEngine
    with tempfile.TemporaryDirectory() as d:
        eng = MemoryEngine(db_path=os.path.join(d, "test.db"))
        tid = eng.add_task("test_task", phase="P2", priority=1, description="test")
        assert tid is not None, "add_task returned None"
        eng.update_task_status(tid, "done")
        tasks = eng.list_tasks(status="done")
        assert any(t.get("name") == "test_task" for t in tasks), \
            f"test_task not in done tasks: {tasks}"
    return True, "task lifecycle: add → update → list"

def test_memory_search():
    from CORE.memory_engine import MemoryEngine
    with tempfile.TemporaryDirectory() as d:
        eng = MemoryEngine(db_path=os.path.join(d, "test.db"))
        eng.store_episode("findable_marker_xyz", context="search_test", result="found_ok")
        results = eng.recall("findable_marker_xyz")
        assert len(results) >= 1, f"recall search returned nothing: {results}"
    return True, "recall() full-text search finds stored episodes"
