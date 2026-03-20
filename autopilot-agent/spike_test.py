"""
Technical Spike — ADR-001 + ADR-003 + ADR-005 验证
验证目标:
  1. LangGraph fan-out: 多个节点并行执行，状态正确汇聚
  2. SqliteSaver checkpointing: 状态持久化且可恢复
  3. SQLite WAL 并发写入: 多个并发写入无死锁
"""

import asyncio
import sqlite3
import time
import os
from typing import TypedDict, Annotated
from operator import add

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver


# ============================================================
# Spike 1: LangGraph fan-out + SqliteSaver checkpointing
# ============================================================

class FanOutState(TypedDict):
    task_ids: list[int]
    results: Annotated[list[str], add]  # fan-in via reducer


def create_worker(worker_id: int):
    """Simulate an agent node (no real LLM call)."""
    def worker(state: FanOutState) -> dict:
        time.sleep(0.1)  # simulate LLM latency
        return {"results": [f"worker-{worker_id} done"]}
    return worker


def route_to_workers(state: FanOutState) -> list[str]:
    """Fan-out: route to N parallel worker nodes."""
    return [f"worker_{i}" for i in state["task_ids"]]


def collect_results(state: FanOutState) -> dict:
    """Fan-in: collect all worker results."""
    return {"results": [f"collected {len(state['results'])} results"]}


def test_spike_1_fanout_checkpoint():
    """Test LangGraph fan-out with SqliteSaver."""
    print("\n" + "=" * 60)
    print("Spike 1: LangGraph fan-out + SqliteSaver checkpointing")
    print("=" * 60)

    db_path = "/tmp/spike_test_checkpoint.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    # Build graph with fan-out
    builder = StateGraph(FanOutState)

    # Add worker nodes
    for i in range(3):
        builder.add_node(f"worker_{i}", create_worker(i))

    builder.add_node("collect", collect_results)

    # Fan-out from START to workers
    builder.add_conditional_edges(START, route_to_workers)

    # Fan-in from workers to collect
    for i in range(3):
        builder.add_edge(f"worker_{i}", "collect")

    builder.add_edge("collect", END)

    # Test with SqliteSaver
    with SqliteSaver.from_conn_string(db_path) as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "spike-1"}}
        initial_state = {"task_ids": [0, 1, 2], "results": []}

        print(f"  Input: task_ids={initial_state['task_ids']}")

        result = graph.invoke(initial_state, config)

        print(f"  Output results: {result['results']}")
        assert len(result["results"]) == 4, f"Expected 4 results (3 workers + 1 collect), got {len(result['results'])}"

        # Verify checkpoint persistence
        state_snapshot = graph.get_state(config)
        assert state_snapshot is not None, "Checkpoint state should not be None"
        print(f"  Checkpoint restored: {state_snapshot.values.get('results', [])[:2]}...")

    print("  ✅ Spike 1 PASSED: fan-out + checkpointing works")
    return True


# ============================================================
# Spike 2: SQLite WAL concurrent writes
# ============================================================

def test_spike_2_sqlite_wal_concurrent():
    """Test SQLite WAL mode with concurrent writes."""
    print("\n" + "=" * 60)
    print("Spike 2: SQLite WAL concurrent writes")
    print("=" * 60)

    db_path = "/tmp/spike_test_wal.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create DB with WAL mode
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mdus (
            id INTEGER PRIMARY KEY,
            worker_id INTEGER,
            status TEXT,
            result TEXT,
            updated_at REAL
        )
    """)
    conn.commit()
    conn.close()

    errors = []
    write_counts = [0] * 5

    def concurrent_writer(worker_id: int, num_writes: int):
        """Simulate an Agent writing to the DB concurrently."""
        local_conn = sqlite3.connect(db_path)
        local_conn.execute("PRAGMA journal_mode=WAL")
        local_conn.execute("PRAGMA busy_timeout=5000")
        try:
            for i in range(num_writes):
                local_conn.execute(
                    "INSERT INTO mdus (worker_id, status, result, updated_at) VALUES (?, ?, ?, ?)",
                    (worker_id, "completed", f"result-{worker_id}-{i}", time.time())
                )
                local_conn.commit()
                write_counts[worker_id] += 1
                time.sleep(0.01)  # simulate work
        except Exception as e:
            errors.append(f"Worker {worker_id}: {e}")
        finally:
            local_conn.close()

    import threading
    threads = []
    num_workers = 5
    writes_per_worker = 20

    print(f"  Starting {num_workers} concurrent writers, {writes_per_worker} writes each...")
    start = time.time()

    for w in range(num_workers):
        t = threading.Thread(target=concurrent_writer, args=(w, writes_per_worker))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed = time.time() - start

    # Verify
    conn = sqlite3.connect(db_path)
    row_count = conn.execute("SELECT COUNT(*) FROM mdus").fetchone()[0]
    conn.close()

    expected = num_workers * writes_per_worker
    print(f"  Duration: {elapsed:.2f}s")
    print(f"  Errors: {len(errors)}")
    for e in errors:
        print(f"    ❌ {e}")
    print(f"  Rows written: {row_count}/{expected}")
    print(f"  Per-worker counts: {write_counts}")

    assert len(errors) == 0, f"Got {len(errors)} errors: {errors}"
    assert row_count == expected, f"Expected {expected} rows, got {row_count}"

    print("  ✅ Spike 2 PASSED: SQLite WAL concurrent writes work")
    return True


# ============================================================
# Run all spikes
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TECHNICAL SPIKE VERIFICATION")
    print("ADR-001 (LangGraph) + ADR-003 (SQLite WAL) + ADR-005 (Concurrency)")
    print("=" * 60)

    results = {}

    try:
        results["spike_1"] = test_spike_1_fanout_checkpoint()
    except Exception as e:
        print(f"  ❌ Spike 1 FAILED: {e}")
        results["spike_1"] = False

    try:
        results["spike_2"] = test_spike_2_sqlite_wal_concurrent()
    except Exception as e:
        print(f"  ❌ Spike 2 FAILED: {e}")
        results["spike_2"] = False

    print("\n" + "=" * 60)
    print("SPIKE RESULTS SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {name}: {status}")

    all_passed = all(results.values())
    print(f"\nOverall: {'✅ ALL SPIKES PASSED' if all_passed else '❌ SOME SPIKES FAILED'}")
