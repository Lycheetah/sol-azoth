AZOTH Capability Tests — 2026-06-27 20:14
PASS: 43  FAIL: 0  SKIP: 0  TOTAL: 43

## test_memory
  ✓ test_memory_capability_register  [90ms]  register_capability + list_capabilities
  ✓ test_memory_engine_importable  [0ms]  MemoryEngine class importable
  ✓ test_memory_episode_store_recall  [90ms]  store_episode + recent_episodes roundtrip
  ✓ test_memory_learn_recall  [82ms]  learn + recall_learnings roundtrip
  ✓ test_memory_search  [86ms]  recall() full-text search finds stored episodes
  ✓ test_memory_task_lifecycle  [91ms]  task lifecycle: add → update → list
## test_memory_summarizer
  ✓ test_compress_over_threshold  [779ms]  compressed 50 episodes, 60 remain
  ✓ test_double_compress  [1090ms]  double compress: 160 → 110 → 60 episodes, 2 summaries
  ✓ test_no_compress_under_threshold  [198ms]  no compression when count < threshold
  ✓ test_status_report  [394ms]  status(): episodes=50, needs_compress=False
  ✓ test_summarizer_importable  [0ms]  summarize + maybe_summarize + recall_summaries + status importable
  ✓ test_summary_content_quality  [796ms]  summary insight contains actions + failure info
  ✓ test_summary_stored_as_learning  [753ms]  summary stored as learning, insight contains batch header
## test_scheduler
  ✓ test_enable_disable  [604ms]  disable blocked runs, enable allowed them (count=2)
  ✓ test_failure_captured  [503ms]  failure captured, ping sent: '◆ scheduler: bad_task FAILED — ValueError: boom'
  ✓ test_log_populated  [402ms]  log has 4 entries, last=ok
  ✓ test_one_shot  [504ms]  one-shot fired 1 time(s) then disabled
  ✓ test_register_and_list  [0ms]  registered 2 tasks: ['task_a', 'task_b']
  ✓ test_scheduler_importable  [0ms]  Scheduler + get/reset importable
  ✓ test_status_shape  [0ms]  status() has correct shape: ['log_entries', 'running', 'task_count', 'tasks']
  ✓ test_task_runs  [101ms]  task ran, status=ok, run_count=1
  ✓ test_unregister  [0ms]  unregister removes task
## test_scratchpad
  ✓ test_scratchpad_blocker  [5ms]  add_blocker + get_blockers
  ✓ test_scratchpad_importable  [0ms]  Scratchpad class importable
  ✓ test_scratchpad_next_step  [2ms]  next_step returns first pending step: action='alpha'
  ✓ test_scratchpad_persists  [2ms]  task survives across Scratchpad instances (file-backed)
  ✓ test_scratchpad_plan  [1ms]  set_plan + get_plan roundtrip
  ✓ test_scratchpad_session  [1ms]  start_session + get_session_id
  ✓ test_scratchpad_task  [1ms]  set_task + get_task roundtrip
## test_tool_loader
  ✓ test_custom_tool_roundtrip  [4ms]  custom tool registered + called successfully
  ✓ test_tool_call_hello  [1ms]  call_tool('hello') returned: {'result': {'message': '◆ Mac — the Athanor burns. What shal
  ✓ test_tool_hello_exists  [1ms]  hello tool present: ['hello']
  ✓ test_tool_loader_discovers_tools  [1ms]  discovered 1 tool(s): ['hello']
  ✓ test_tool_loader_importable  [0ms]  discover_tools + list_tools + call_tool importable
## test_truth_pressure
  ✓ test_forge_gates_fail_no_file  [5ms]  forge_gates correctly reports gate1 fail for missing file
  ✓ test_forge_gates_pass  [0ms]  forge_gates returns dict: gate1=True
  ✓ test_pi_gate2  [0ms]  gate2_pass()=True with high evidence (threshold=1.0)
  ✓ test_pi_rises_with_evidence  [0ms]  Π rises to 2.700 after recording evidence+precision
  ✓ test_pi_summary  [0ms]  summary() returns pi=1.600, claims=1
  ✓ test_pi_zero_at_start  [0ms]  fresh tracker returns Π=0.000
  ✓ test_register_enum_has_all_types  [0ms]  Register has all 7 types: ['ASSUMED', 'CONJECTURE', 'CONSISTENCY', 'DERIVED', 'INTERPRETIVE', 'INTUITION', 'MEASURED']
  ✓ test_score_function  [0ms]  score(E=3, P=0.9, S=0.0, s0=1.0) = Π=2.700
  ✓ test_truth_pressure_importable  [0ms]  PiTracker + forge_gates + Register + score importable

ALL TESTS PASS — forge gate clear