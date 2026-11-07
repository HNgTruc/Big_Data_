"""Tests for src/experiments (host side, no Docker, no Spark): statistics, commands, cluster checks,
runner records, event-log parsing and the analysis tables."""
import json
import subprocess
import sys

import pytest

from src.experiments.common import analysis as A
from src.experiments.common import cluster, commands, eventlog, host, paths, records, runner, stats
from src.experiments.common.runner import Runner, RunnerOptions, RunSpec


# ---- statistics ---------------------------------------------------------------------------

def test_summarize_uses_sample_std_and_skips_missing():
    s = stats.summarize([1.0, 2.0, 3.0, None, float("nan")])
    assert s == {"n": 3, "mean": 2.0, "std": 1.0, "min": 1.0, "max": 3.0}


def test_summarize_single_and_empty():
    assert stats.summarize([5.0])["std"] is None
    assert stats.summarize([]) == {"n": 0, "mean": None, "std": None, "min": None, "max": None}


def test_speedup_efficiency_throughput():
    s = stats.speedup(120.0, 80.0)
    assert s == pytest.approx(1.5)
    assert stats.efficiency(s, 2) == pytest.approx(0.75)
    assert stats.speedup(None, 80.0) is None and stats.speedup(120.0, 0) is None
    assert stats.efficiency(None, 2) is None
    assert stats.throughput(1_000, 4.0) == 250.0
    assert stats.throughput(1_000, 0) is None
    assert stats.relative_to_first([2.0, 4.0, None]) == [1.0, 2.0, None]


# ---- commands -----------------------------------------------------------------------------

def test_etl_command_matches_infra_readme_prefix():
    spec = RunSpec(exp="scale_data", config="orders_500k", kind="etl", dataset="orders_500k")
    cmd, cwd = runner.build_command(spec, 2, RunnerOptions())
    assert cwd == paths.INFRA_DIR
    assert cmd[:7] == ["docker", "compose", "run", "--rm", "--no-deps", "--name", "etl-driver"]
    assert "exec" not in cmd
    joined = " ".join(cmd)
    assert ("spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 "
            "--conf spark.driver.host=etl-driver --conf spark.jars.ivy=/opt/spark/work-dir/data/ivy_cache "
            "--packages org.apache.hadoop:hadoop-aws:3.4.1 /opt/spark/work-dir/src/etl/etl_job.py") in joined
    # without the cache the command is exactly the one documented in infra/README.md
    plain, _ = runner.build_command(spec, 2, RunnerOptions(ivy_cache=False))
    assert "spark.jars.ivy=/tmp/.ivy" in plain
    tail = cmd[cmd.index("/opt/spark/work-dir/src/etl/etl_job.py") + 1:]
    assert tail == ["--dataset", "orders_500k", "--run-label", "scale_data_orders_500k", "--metrics-dir",
                    "/opt/spark/work-dir/results/metrics/scale_data/runs/orders_500k/r2"]
    assert "spark.eventLog.enabled=true" not in cmd


def test_event_log_conf_and_extra_args():
    spec = RunSpec(exp="join_strategy", config="shuffle_noauto", kind="etl", dataset="orders_5m",
                   args=("--join-strategy", "shuffle", "--no-auto-broadcast"), event_log=True,
                   spark_conf=("spark.sql.adaptive.advisoryPartitionSizeInBytes=2097152",))
    cmd, _ = runner.build_command(spec, 1, RunnerOptions())
    assert "-v" not in cmd  # data/ is already mounted; no extra volume
    i = cmd.index("spark.sql.adaptive.advisoryPartitionSizeInBytes=2097152")
    assert cmd[i - 1] == "--conf" and i < cmd.index("--packages")
    assert "spark.eventLog.dir=file:///opt/spark/work-dir/results/logs/join_strategy/eventlogs" in cmd
    assert "spark.eventLog.compress=false" in cmd and "spark.eventLog.rolling.enabled=false" in cmd
    assert cmd[-3:] == ["--join-strategy", "shuffle", "--no-auto-broadcast"]


def test_query_bench_and_pandas_commands():
    qb = RunSpec(exp="cache", config="cache", kind="query_bench", dataset="orders_5m",
                 args=("cache", "--dataset", "orders_5m", "--mode", "cache"))
    cmd, cwd = runner.build_command(qb, 3, RunnerOptions())
    assert "bench-driver" in cmd and "spark.driver.host=bench-driver" in cmd
    assert cmd[-2:] == ["--out", "/opt/spark/work-dir/results/metrics/cache/runs/cache/r3/query_bench.json"]
    pd_spec = RunSpec(exp="pandas_baseline", config="orders_1m", kind="pandas", dataset="orders_1m", workers=None)
    cmd, cwd = runner.build_command(pd_spec, 1, RunnerOptions(python="py"))
    assert cwd == paths.REPO_ROOT
    assert cmd[:5] == ["py", "-m", "src.experiments.pandas_baseline.baseline", "--dataset", "orders_1m"]
    assert cmd[-1].endswith("pandas_baseline.json")


def test_compose_and_minio_guards():
    assert commands.compose_service("stop", "spark-worker-2") == ["docker", "compose", "stop", "spark-worker-2"]
    with pytest.raises(ValueError):
        commands.compose_service("rm", "spark-worker-2")
    cmd = commands.minio_remove("bigdata", "curated/x_y", "quarantine/x_y")
    assert cmd[-2:] == ["local/bigdata/curated/x_y/", "local/bigdata/quarantine/x_y/"]  # trailing slash
    assert "exec" not in cmd
    for bad in ("", "/", "curated/../raw", "curated"):
        with pytest.raises(ValueError):
            commands.minio_remove("bigdata", bad)
    with pytest.raises(ValueError):
        commands.minio_remove("bigdata")
    with pytest.raises(ValueError):
        commands.spark_submit("x.py", [], "d", commands.SparkSubmitOptions(spark_conf=("novalue",)))


def test_plan_orders():
    a = RunSpec(exp="e", config="a", kind="etl", dataset="d")
    b = RunSpec(exp="e", config="b", kind="etl", dataset="d")
    assert [(s.config, r) for s, r in runner.plan_runs([a, b], 2, "interleaved")] == [
        ("a", 1), ("b", 1), ("a", 2), ("b", 2)]
    assert [(s.config, r) for s, r in runner.plan_runs([a, b], 2, "blocked")] == [
        ("a", 1), ("a", 2), ("b", 1), ("b", 2)]
    with pytest.raises(ValueError):
        runner.plan_runs([a], 0, "blocked")


# ---- cluster ------------------------------------------------------------------------------

MASTER = {"workers": [{"id": "w1", "cores": 2, "memory": 2048, "state": "ALIVE"},
                      {"id": "w2", "cores": 2, "memory": 2048, "state": "DEAD"},
                      {"id": "w3", "cores": 2, "memory": 2048, "state": "ALIVE"}],
          "activeapps": [], "status": "ALIVE"}


def test_only_alive_workers_count():
    snap = cluster.parse_master_json(MASTER)
    assert snap.alive_workers == 2 and snap.total_alive_cores == 4
    cluster.check_expected(snap, 2, 2)
    with pytest.raises(cluster.ClusterStateError):
        cluster.check_expected(snap, 1, 2)
    with pytest.raises(cluster.ClusterStateError):
        cluster.check_expected(snap, 2, 3)
    busy = cluster.parse_master_json({**MASTER, "activeapps": [{"id": "app"}]})
    with pytest.raises(cluster.ClusterStateError):
        cluster.check_expected(busy, 2, 2)


def test_worker_controller_dry_run_restores():
    ctl = cluster.WorkerController("http://x", log=lambda m: None, dry_run=True)
    ctl.ensure(1)
    ctl.ensure(1)
    ctl.ensure(2)
    ctl.ensure(1)
    ctl.restore()
    ctl.restore()
    assert ctl.actions == ["stop", "start", "stop", "start"]


def test_worker_controller_refuses_unexpected_state(monkeypatch):
    one_alive = cluster.parse_master_json({"workers": [MASTER["workers"][0]], "activeapps": []})
    monkeypatch.setattr(cluster, "fetch_snapshot", lambda url, timeout=5.0: one_alive)
    ctl = cluster.WorkerController("http://x", log=lambda m: None)
    with pytest.raises(cluster.ClusterStateError):
        ctl.ensure(1)  # only 1 ALIVE before we stopped anything: do not guess which one is missing
    assert ctl.actions == []


def test_worker_flag_set_before_stop(monkeypatch):
    two = cluster.parse_master_json({"workers": [MASTER["workers"][0], MASTER["workers"][2]], "activeapps": []})
    monkeypatch.setattr(cluster, "fetch_snapshot", lambda url, timeout=5.0: two)
    monkeypatch.setattr(cluster.subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a, 1, stdout="", stderr="boom"))
    ctl = cluster.WorkerController("http://x", log=lambda m: None)
    with pytest.raises(cluster.ClusterStateError):
        ctl.ensure(1)
    assert ctl.stopped_worker_2  # so the runner's finally still runs `start`


def test_foreign_containers_parsing():
    text = "bigdata-minio-1\tbigdata\nxom-nho-mysql\txom-nho\nlonely\t\n"
    assert host.parse_containers(text) == ["lonely", "xom-nho-mysql"]
    assert "method" in host.memory_status()


# ---- runner and records -------------------------------------------------------------------

@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(paths, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(paths, "RAW_DIR", tmp_path / "data" / "raw")
    manifest = tmp_path / "data" / "raw" / "ds" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"params": {"seed": 42, "skew": False},
                                    "rows_written": {"orders": 10, "order_items": 20}}), encoding="utf-8")
    return tmp_path


def _fake_job(monkeypatch, exit_code: int, write_metrics: bool):
    """Replace the docker/pandas command with a tiny Python process."""
    def build(spec, rep, opts):
        out = paths.run_dir(spec.exp, spec.config, rep) / spec.metrics_file()
        code = ("import json, pathlib; print('job output'); "
                + (f"pathlib.Path(r'{out}').write_text(json.dumps({{'processing_seconds_total': 1.5, "
                   f"'stage_seconds': {{'orders': 1.5}}, 'app_id': 'app-1'}}));" if write_metrics else "")
                + f"raise SystemExit({exit_code})")
        return [sys.executable, "-c", code], paths.REPO_ROOT
    monkeypatch.setattr(runner, "build_command", build)


def _host_spec():
    return RunSpec(exp="exp", config="cfg", kind="pandas", dataset="ds", workers=None)


def test_runner_writes_ok_record_and_log(tmp_repo, monkeypatch):
    _fake_job(monkeypatch, 0, True)
    status = Runner("exp", "t", [_host_spec()], RunnerOptions(reps=2), out=lambda m: None).run()
    assert status == 0
    recs = records.load_records("exp")
    assert [r["rep"] for r in recs] == [1, 2]
    r = recs[0]
    assert r["status"] == "ok" and r["processing_seconds_total"] == 1.5 and r["seed"] == 42
    assert r["raw_rows_total_manifest"] == 30 and r["wall_seconds"] > 0
    assert r["started_at"] <= r["ended_at"] and r["git"] is not None
    assert "job output" in (tmp_repo / r["log_path"]).read_text(encoding="utf-8")
    for sub in ("metrics/exp", "metrics/exp/runs", "logs/exp", "figures/exp"):
        assert (tmp_repo / "results" / sub / "README.md").exists()


def test_runner_records_failures_and_protects_old_records(tmp_repo, monkeypatch):
    _fake_job(monkeypatch, 3, False)
    assert Runner("exp", "t", [_host_spec()], RunnerOptions(reps=1), out=lambda m: None).run() == 1
    rec = records.load_records("exp")[0]
    assert rec["status"] == "failed" and rec["exit_code"] == 3 and rec["error"] == "exit code 3"
    # a second run without --overwrite/--resume is refused
    assert Runner("exp", "t", [_host_spec()], RunnerOptions(reps=1), out=lambda m: None).run() == 2
    # --resume re-runs the failed rep and keeps the failed record under a timestamped name
    _fake_job(monkeypatch, 0, True)
    assert Runner("exp", "t", [_host_spec()], RunnerOptions(reps=1, resume=True), out=lambda m: None).run() == 0
    assert records.load_records("exp")[0]["status"] == "ok"
    assert A.archived_attempts("exp") == 1
    # --resume now skips the successful rep
    lines = []
    Runner("exp", "t", [_host_spec()], RunnerOptions(reps=1, resume=True), out=lines.append).run()
    assert any("skip cfg r1" in ln for ln in lines)


def test_ok_without_metrics_is_failure(tmp_repo, monkeypatch):
    _fake_job(monkeypatch, 0, False)
    Runner("exp", "t", [_host_spec()], RunnerOptions(reps=1), out=lambda m: None).run()
    rec = records.load_records("exp")[0]
    assert rec["status"] == "failed" and "missing" in rec["error"]


def test_dry_run_writes_nothing(tmp_repo):
    lines = []
    spec = RunSpec(exp="exp", config="w1", kind="etl", dataset="ds", workers=1)
    assert Runner("exp", "t", [spec], RunnerOptions(reps=1, dry_run=True), out=lines.append).run() == 0
    assert not (tmp_repo / "results").exists()
    text = "\n".join(lines)
    assert "docker compose stop spark-worker-2" in text and "docker compose start spark-worker-2" in text


def test_etl_pre_cleanup_runs_outside_the_timed_command(tmp_repo, monkeypatch):
    calls = []

    def fake_run(cmd, *a, **k):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    _fake_job(monkeypatch, 0, True)
    spec = RunSpec(exp="exp", config="cfg", kind="etl", dataset="ds", workers=None)
    Runner("exp", "t", [spec], RunnerOptions(reps=1), out=lambda m: None).run()
    rm = [c for c in calls if "rm" in c and "minio-init" in c]
    assert rm and rm[0][-2:] == ["local/bigdata/curated/exp_cfg/", "local/bigdata/quarantine/exp_cfg/"]
    rec = records.load_records("exp")[0]
    assert rec["pre_cleanup"]["exit_code"] == 0 and rec["pre_cleanup"]["seconds"] >= 0
    assert "pre_cleanup_failed" not in A.run_flags(rec)


def test_parse_ivy_times():
    log = ":: resolution report :: resolve 6546ms :: artifacts dl 54020ms\n"
    assert records.parse_ivy_times(log) == {"resolve_ms": 6546, "download_ms": 54020}
    assert records.parse_ivy_times("nothing") == {}


# ---- event logs ---------------------------------------------------------------------------

def _plan(*names):
    node = {"nodeName": "Scan", "children": []}
    for n in names:
        node = {"nodeName": n, "simpleString": "", "children": [node]}
    return node


def test_reused_exchange_not_counted_twice():
    original = _plan("SortMergeJoin", "Exchange")
    plan = {"nodeName": "Union", "children": [original, {"nodeName": "ReusedExchange", "children": [original]}]}
    counts = eventlog.count_nodes(plan)
    assert counts["SortMergeJoin"] == 1 and counts["ReusedExchange"] == 1
    skewed_read = {"nodeName": "AQEShuffleRead", "simpleString": "AQEShuffleRead coalesced and skewed",
                   "children": []}
    skew = eventlog.join_summary({1: _plan("ShuffledHashJoin(skew=true)"), 2: skewed_read})
    assert skew["ShuffledHashJoin(skew=true)"] == 1 and skew["AQEShuffleRead(skewed)"] == 1


def test_event_log_last_plan_wins(tmp_path):
    lines = [
        json.dumps({"Event": eventlog.START, "executionId": 1, "sparkPlanInfo": _plan("SortMergeJoin")}),
        json.dumps({"Event": "SparkListenerTaskEnd", "Task Info": {}}),
        json.dumps({"Event": eventlog.AQE_UPDATE, "executionId": 1, "sparkPlanInfo": _plan("BroadcastHashJoin")}),
        json.dumps({"Event": eventlog.START, "executionId": 2,
                    "sparkPlanInfo": _plan("SortMergeJoin(skew=true)", "SortMergeJoin")}),
        '{"Event": "org.apache.spark.sql.execution.ui.SparkListenerSQLExecutionStart", "trunc',
    ]
    path = tmp_path / "app-1"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = eventlog.summarize_file(path)
    assert summary["BroadcastHashJoin"] == 1 and summary["SortMergeJoin"] == 1
    assert summary["SortMergeJoin(skew=true)"] == 1 and summary["executions"] == 2


def test_event_log_rejects_compressed_dir(tmp_path):
    d = tmp_path / "eventlog_v2_app-1"
    d.mkdir()
    (d / "events_1_app-1.zstd").write_bytes(b"\x28\xb5")
    with pytest.raises(ValueError):
        eventlog.summarize_file(d)


# ---- analysis -----------------------------------------------------------------------------

def _etl_record(config, rep, status, seconds, raw=(100, 200)):
    return {"exp": "x", "config": config, "rep": rep, "dataset": "d", "status": status, "exit_code": 0,
            "wall_seconds": seconds + 60, "processing_seconds_total": seconds if status == "ok" else None,
            "stage_seconds": {"orders": seconds / 2, "order_items": seconds / 2} if status == "ok" else None,
            "metrics": {"tables": {"orders": {"raw_rows": raw[0]}, "order_items": {"raw_rows": raw[1]}}}
            if status == "ok" else None}


def test_summary_uses_only_successful_runs():
    rows = [A.etl_run_row(r) for r in (_etl_record("a", 1, "ok", 10), _etl_record("a", 2, "ok", 20),
                                       _etl_record("a", 3, "failed", 0))]
    assert rows[0]["throughput_rows_per_s"] == 30.0
    summary = A.summary_rows(rows, ["config"], ["processing_seconds_total"])
    assert summary[0]["n"] == 2 and summary[0]["n_failed"] == 1 and summary[0]["mean"] == 15.0


def test_scale_workers_speedup_and_analyze(tmp_path):
    from src.experiments.scale_workers import analyze as sw
    base = tmp_path / "results" / "metrics" / "scale_workers" / "runs"
    for config, times in (("w1", (100, 110, 90)), ("w2", (60, 50, 40))):
        for rep, t in enumerate(times, 1):
            rec = {**_etl_record(config, rep, "ok", t), "exp": "scale_workers"}
            records.write_record(base / config / f"r{rep}", rec)
    summary = sw.analyze(tmp_path / "results")
    row = A.lookup(summary, "processing_seconds_total", config="w2")
    assert row["speedup"] == pytest.approx(2.0) and row["efficiency"] == pytest.approx(1.0)
    assert row["std"] == pytest.approx(10.0)
    assert (tmp_path / "results" / "metrics" / "scale_workers" / "summary.csv").exists()
    csv_rows = A.read_csv(tmp_path / "results" / "metrics" / "scale_workers" / "runs.csv")
    assert len(csv_rows) == 6


def test_scale_data_ratios():
    from src.experiments.scale_data import analyze as sd
    recs = [_etl_record("small", 1, "ok", 10, (100, 100)), _etl_record("big", 1, "ok", 30, (400, 400))]
    rows = [A.etl_run_row(r) for r in recs]
    summary = A.summary_rows(rows, ["config"], A.etl_metric_names())
    assert sd.scaling_columns(summary, rows) == ["small", "big"]
    big = A.lookup(summary, "processing_seconds_total", config="big")
    assert big["data_ratio"] == 4.0 and big["time_ratio"] == 3.0


def test_format_and_cache_summaries():
    from src.experiments.cache import analyze as ca
    from src.experiments.format_compare import analyze as fc
    def rec(config, order, raw_s, cur_s, rep=1):
        return {"config": config, "rep": rep, "dataset": "d", "status": "ok", "kind": "query_bench",
                "metrics": {"format_order": order, "measurements": [
                    {"query": "q1", "format": "raw", "seconds": raw_s},
                    {"query": "q1", "format": "curated", "seconds": cur_s}]}}
    rows = fc.query_rows([rec("raw_first", ["raw", "curated"], 4.0, 1.0),
                          rec("curated_first", ["curated", "raw"], 2.0, 1.0)])
    summary = fc.summarize_queries(rows)  # both orders pooled
    raw = next(s for s in summary if s["format"] == "raw")
    assert raw["n"] == 2 and raw["ratio_raw_over_curated"] == 3.0
    by_order = fc.summarize_queries(rows, by_order=True)
    assert {r["order"] for r in by_order} == {"raw-curated", "curated-raw"}
    summary = [{"config": "nocache", "step": "queries_seconds_total", "mean": 50.0},
               {"config": "cache", "step": "queries_seconds_total", "mean": 10.0},
               {"config": "cache", "step": "materialize_seconds", "mean": 16.0}]
    be = ca.break_even(summary, 5)
    assert be["per_query_saving"] == 8.0 and be["break_even_queries"] == 2.0
    assert be["break_even_queries_ceil"] == 2 and be["saving_at_k"] == 50.0 - 26.0
    slower = [dict(r) for r in summary]
    slower[1]["mean"] = 60.0
    assert ca.break_even(slower, 5)["break_even_queries"] is None


def _full(config, rep, seconds, **extra):
    rec = {**_etl_record(config, rep, "ok", seconds), "kind": "etl", "workers_expected": 2,
           "cluster_after": {"alive_workers": 2}, "git": {"commit": "a" * 40, "dirty": False},
           "raw_rows_manifest": {"orders": 100, "order_items": 200}, "runner_options": {"ivy_cache": True}}
    rec.update(extra)
    return rec


def test_flags_exclude_bad_runs_but_keep_them_visible():
    recs = [_full("a", 1, 10), _full("a", 2, 20),
            _full("a", 3, 99, cluster_after={"alive_workers": 1}),
            _full("a", 4, 50, raw_rows_manifest={"orders": 101, "order_items": 200}),
            _full("a", 5, 30, host_before={"foreign_containers": ["xom-nho-mysql"]})]
    rows = [A.etl_run_row(r) for r in recs]
    assert [r["valid"] for r in rows] == [True, True, False, False, True]
    assert "workers_changed" in rows[2]["flags"] and "raw_rows_mismatch" in rows[3]["flags"]
    assert rows[4]["flags"] == "foreign_containers"
    s = A.lookup(A.summary_rows(rows, ["config"], ["processing_seconds_total"]), "processing_seconds_total",
                 config="a")
    assert s["n"] == 3 and s["n_excluded"] == 2 and s["mean"] == 20.0
    assert s["homogeneous"] is True and s["git_commits"] == "a" * 10 and s["dirty_any"] is False


def test_quality_detects_mixed_commits_and_inconsistent_counts():
    other = _full("a", 2, 20, git={"commit": "b" * 40, "dirty": True})
    other["metrics"]["tables"]["orders"]["clean_rows"] = 5
    rows = [A.etl_run_row(r) for r in (_full("a", 1, 10), other)]
    s = A.summary_rows(rows, ["config"], ["processing_seconds_total"])[0]
    assert s["homogeneous"] is False and s["dirty_any"] is True and s["counts_consistent"] is False
    assert A.warn_quality("x", [s])


def test_new_experiment_plans():
    import argparse
    from src.experiments.format_compare import run as fc_run
    from src.experiments.join_strategy import run as js_run
    from src.experiments.skew import run as sk_run

    def specs(mod, argv=()):
        p = argparse.ArgumentParser()
        mod.add_args(p)
        return mod.build_specs(p.parse_args(list(argv)))
    assert [s.config for s in specs(js_run)] == ["auto", "broadcast", "shuffle_noauto"]
    assert [s.config for s in specs(fc_run)] == ["raw_first", "curated_first"]
    sk = {s.config: s for s in specs(sk_run)}
    assert len(sk) == 8
    forced = sk["skew_shuffle_aqe"]
    assert forced.dataset == "orders_5m_skew" and "--no-aqe" not in forced.args
    assert forced.args[:5] == ("--join-strategy", "shuffle", "--no-auto-broadcast", "--shuffle-partitions", "64")
    assert forced.spark_conf == ("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes=4194304",
                                 "spark.sql.adaptive.advisoryPartitionSizeInBytes=2097152")
    assert sk["balanced_auto_noaqe"].args == ("--join-strategy", "auto", "--no-aqe")
    assert sk["balanced_auto_noaqe"].spark_conf == ()
    with pytest.raises(SystemExit):
        specs(sk_run, ["--skew-threshold-bytes", "1", "--advisory-bytes", "2"])
