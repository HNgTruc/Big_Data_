"""Run the repetitions of an experiment: checks, docker/subprocess call, log, run record.

Every repetition writes `results/metrics/<exp>/runs/<config>/r<k>/run_record.json` (also when it
fails) and its stdout/stderr to `results/logs/<exp>/<config>_r<k>.log`. A previous record or log of
the same repetition is renamed with a timestamp, never deleted.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Sequence

from . import cluster, commands, paths, records

KINDS = ("etl", "query_bench", "pandas")
METRICS_FILE = {"query_bench": "query_bench.json", "pandas": "pandas_baseline.json"}
PANDAS_MODULE = "src.experiments.pandas_baseline.baseline"


@dataclass(frozen=True)
class RunSpec:
    """One configuration of an experiment (repeated `reps` times)."""

    exp: str
    config: str
    kind: str                         # etl | query_bench | pandas
    dataset: str
    workers: int | None = 2           # ALIVE workers required; None = host-only run
    args: tuple[str, ...] = ()        # extra job arguments
    event_log: bool = False
    params: dict = field(default_factory=dict)  # descriptive configuration saved in the record

    @property
    def label(self) -> str:
        """Run label: curated/<label>/ on MinIO; identical for all repetitions (overwritten)."""
        return f"{self.exp}_{self.config}"

    def metrics_file(self) -> str:
        return METRICS_FILE.get(self.kind, f"{self.label}.json")


@dataclass
class RunnerOptions:
    reps: int = 3
    dry_run: bool = False
    order: str = "interleaved"        # interleaved | blocked
    overwrite: bool = False
    resume: bool = False
    timeout_s: float = 3600.0
    master_url: str = "http://localhost:8090/json/"
    cores_per_worker: int | None = 2
    ivy_cache: Path | None = None
    bucket: str = "bigdata"
    hadoop_aws_version: str = "3.4.1"
    python: str = sys.executable
    stop_on_failure: bool = False
    cleanup_curated: bool = False


def plan_runs(specs: Sequence[RunSpec], reps: int, order: str) -> list[tuple[RunSpec, int]]:
    """(spec, rep) pairs. Interleaved spreads slow drift of the machine over all configurations."""
    if reps < 1:
        raise ValueError("reps must be >= 1")
    if order == "interleaved":
        return [(s, r) for r in range(1, reps + 1) for s in specs]
    if order == "blocked":
        return [(s, r) for s in specs for r in range(1, reps + 1)]
    raise ValueError(f"unknown order {order!r}")


def build_command(spec: RunSpec, rep: int, opts: RunnerOptions) -> tuple[list[str], Path]:
    """Command list and working directory of one repetition."""
    rdir = paths.run_dir(spec.exp, spec.config, rep)
    if spec.kind == "pandas":
        cmd = [opts.python, "-m", PANDAS_MODULE, "--dataset", spec.dataset, *spec.args,
               "--metrics-out", str(rdir / spec.metrics_file())]
        return cmd, paths.REPO_ROOT
    submit = commands.SparkSubmitOptions(
        hadoop_aws_version=opts.hadoop_aws_version, ivy_cache=opts.ivy_cache,
        event_log_dir=paths.to_container(paths.logs_dir(spec.exp) / "eventlogs") if spec.event_log else None)
    container_metrics = paths.to_container(rdir)
    if spec.kind == "etl":
        cmd = commands.spark_submit(commands.ETL_SCRIPT,
                                    commands.etl_args(spec.dataset, spec.label, container_metrics, spec.args),
                                    commands.ETL_CONTAINER, submit)
    elif spec.kind == "query_bench":
        cmd = commands.spark_submit(commands.QUERY_BENCH_SCRIPT,
                                    [*spec.args, "--out", f"{container_metrics}/{spec.metrics_file()}"],
                                    commands.BENCH_CONTAINER, submit)
    else:
        raise ValueError(f"unknown run kind {spec.kind!r}; use one of {KINDS}")
    return cmd, paths.INFRA_DIR


def container_name(spec: RunSpec) -> str | None:
    return {"etl": commands.ETL_CONTAINER, "query_bench": commands.BENCH_CONTAINER}.get(spec.kind)


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def _archive(path: Path) -> Path | None:
    """Rename an existing file to `<stem>.<timestamp><suffix>` so older attempts stay on disk."""
    if not path.exists():
        return None
    target = path.with_name(f"{path.stem}.{_stamp()}{path.suffix}")
    path.rename(target)
    return target


def _error_lines(text: str, limit: int = 20) -> list[str]:
    keys = ("Traceback", "Error", "Exception", "QUERY_BENCH_ERROR", "PANDAS_ERROR")
    return [ln.strip() for ln in text.splitlines() if any(k in ln for k in keys)][:limit]


def ensure_result_dirs(exp: str, title: str) -> None:
    """Create results/{metrics,logs,figures}/<exp>/ with a short README each (only if missing)."""
    texts = {
        paths.metrics_dir(exp): (
            f"# metrics/{exp}\n\nSố đo của thí nghiệm `{exp}` ({title}); tạo bởi `src/experiments/{exp}/run.py`.\n\n"
            "| Đường dẫn | Nội dung |\n|---|---|\n"
            "| `runs/<config>/r<k>/run_record.json` | Bản ghi từng lần chạy (kể cả lần lỗi) |\n"
            "| `runs/<config>/r<k>/*.json` | Metrics do job ghi ra |\n"
            "| `runs.csv`, `summary.csv`, ... | Sinh bởi `analyze.py` từ các run record |\n\n"
            "Không sửa tay. Bản ghi cũ của cùng một lần lặp được đổi tên kèm thời điểm, không bị xoá.\n"),
        paths.metrics_dir(exp) / "runs": (
            f"# metrics/{exp}/runs\n\nMỗi cấu hình một thư mục `<config>/`, mỗi lần lặp một thư mục `r<k>/` "
            "chứa `run_record.json` và file metrics của job. Các thư mục con này không có README riêng.\n"),
        paths.logs_dir(exp): (
            f"# logs/{exp}\n\nLog stdout/stderr từng lần chạy (`<config>_r<k>.log`), nhật ký bộ điều khiển "
            "(`runner.log`) và event log của Spark (`eventlogs/`, nếu bật; không đưa lên git).\n"),
        paths.figures_dir(exp): (
            f"# figures/{exp}\n\nHình sinh bởi `src/experiments/{exp}/analyze.py` từ `results/metrics/{exp}/`. "
            "Thanh lỗi = độ lệch chuẩn mẫu; n ghi trên hình.\n"),
    }
    for folder, text in texts.items():
        folder.mkdir(parents=True, exist_ok=True)
        readme = folder / "README.md"
        if not readme.exists():
            readme.write_text(text, encoding="utf-8")


class Runner:
    """Executes a list of RunSpec with the options; one instance per experiment invocation."""

    def __init__(self, exp: str, title: str, specs: Sequence[RunSpec], opts: RunnerOptions,
                 out: Callable[[str], None] = print):
        self.exp, self.title, self.specs, self.opts, self._out = exp, title, list(specs), opts, out
        self.plan = plan_runs(self.specs, opts.reps, opts.order)
        self.runner_log = paths.logs_dir(exp) / "runner.log"

    def log(self, msg: str) -> None:
        line = f"[{records.now_iso()}] [{self.exp}] {msg}"
        self._out(line)
        if not self.opts.dry_run:
            self.runner_log.parent.mkdir(parents=True, exist_ok=True)
            with self.runner_log.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    def _needs_cluster(self) -> bool:
        return any(s.workers is not None for s in self.specs)

    def _existing(self) -> list[Path]:
        return [p for s, r in self.plan
                if (p := paths.run_dir(s.exp, s.config, r) / records.RECORD_NAME).exists()]

    def _done_ok(self, spec: RunSpec, rep: int) -> bool:
        path = paths.run_dir(spec.exp, spec.config, rep) / records.RECORD_NAME
        return path.exists() and records.read_record(path).get("status") == "ok"

    def run(self) -> int:
        """Return 0 if every repetition succeeded, 1 if some failed, 2 if aborted."""
        if self.opts.dry_run:
            return self._dry_run()
        existing = self._existing()
        if existing and not (self.opts.overwrite or self.opts.resume):
            self._out(f"[{self.exp}] {len(existing)} run record(s) already exist, e.g. "
                      f"{paths.rel_to_repo(existing[0])}. Use --resume (skip successful reps) or "
                      "--overwrite (old records are renamed, not deleted).")
            return 2
        ensure_result_dirs(self.exp, self.title)
        git = records.git_info()
        self.log(f"start: {len(self.plan)} run(s), reps={self.opts.reps}, order={self.opts.order}, "
                 f"git={git['commit']} dirty={git['dirty']}")
        workers = cluster.WorkerController(self.opts.master_url, log=self.log)
        failures, status = 0, 0
        try:
            for spec, rep in self.plan:
                if self.opts.resume and self._done_ok(spec, rep):
                    self.log(f"skip {spec.config} r{rep}: already ok (--resume)")
                    continue
                snap = self._preflight(spec, workers)
                record = self._execute(spec, rep, snap, git)
                self.log(f"{spec.config} r{rep}: {record['status']} wall={record['wall_seconds']}s "
                         f"processing={record.get('processing_seconds_total')}")
                if record["status"] != "ok":
                    failures += 1
                    if record["status"] == "timeout" or self.opts.stop_on_failure:
                        self.log("stopping after this failure")
                        status = 2
                        break
        except cluster.ClusterStateError as exc:
            self.log(f"ABORT: {exc}")
            status = 2
        finally:
            try:
                workers.restore()
            except cluster.ClusterStateError as exc:
                self.log(f"ERROR while restoring spark-worker-2: {exc}. "
                         "Run `docker compose start spark-worker-2` in infra/ and check :8090.")
                status = 2
        if self.opts.cleanup_curated and status != 2:
            self.cleanup()
        self.log(f"done: failures={failures} status={status}")
        return status or (1 if failures else 0)

    def _preflight(self, spec: RunSpec, workers: cluster.WorkerController) -> cluster.ClusterSnapshot | None:
        """Check the cluster right before a run; raise ClusterStateError if anything is off."""
        if spec.workers is None:
            return None
        workers.ensure(spec.workers)
        cluster.wait_idle(self.opts.master_url)
        snap = cluster.fetch_snapshot(self.opts.master_url)
        cluster.check_expected(snap, spec.workers, self.opts.cores_per_worker)
        name = container_name(spec)
        if name:
            res = subprocess.run(commands.container_exists(name), capture_output=True, text=True)
            if res.returncode != 0:
                raise cluster.ClusterStateError(f"docker ps failed: {res.stderr.strip()}")
            if res.stdout.strip():
                raise cluster.ClusterStateError(f"a container named {name} already exists; "
                                                f"remove it (`docker rm -f {name}`) after checking it is stale")
        return snap

    def _execute(self, spec: RunSpec, rep: int, snap, git: dict) -> dict:
        rdir = paths.run_dir(spec.exp, spec.config, rep)
        rdir.mkdir(parents=True, exist_ok=True)
        log_path = paths.logs_dir(spec.exp) / f"{spec.config}_r{rep}.log"
        metrics_path = rdir / spec.metrics_file()
        archived = [p for p in (_archive(rdir / records.RECORD_NAME), _archive(log_path), _archive(metrics_path)) if p]
        ev_dir = paths.logs_dir(spec.exp) / "eventlogs"
        if spec.event_log:
            ev_dir.mkdir(parents=True, exist_ok=True)
        ev_before = set(ev_dir.iterdir()) if ev_dir.exists() else set()
        cmd, cwd = build_command(spec, rep, self.opts)
        self.log(f"run {spec.config} r{rep}: {commands.to_display(cmd)}")

        started = records.now_iso()
        t0 = time.perf_counter()
        status, exit_code, error = "failed", None, None
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8", errors="replace") as fh:
            proc = subprocess.Popen(cmd, cwd=cwd, stdout=fh, stderr=subprocess.STDOUT)
            try:
                exit_code = proc.wait(timeout=self.opts.timeout_s)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                status, error = "timeout", f"killed after {self.opts.timeout_s}s"
                name = container_name(spec)
                if name:  # the compose client is gone but the driver container may still run
                    subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True)
        wall = round(time.perf_counter() - t0, 3)
        ended = records.now_iso()

        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        metrics = None
        if metrics_path.exists():
            try:
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            except ValueError as exc:
                error = f"unreadable metrics file: {exc}"
        if status != "timeout":
            if exit_code == 0 and metrics is not None:
                status = "ok"
            elif exit_code == 0:
                error = error or f"exit code 0 but {metrics_path.name} missing"
            else:
                error = error or f"exit code {exit_code}"

        after = None
        if spec.workers is not None:
            try:
                after = cluster.fetch_snapshot(self.opts.master_url).as_record()
            except cluster.ClusterStateError as exc:
                after = {"error": str(exc)}
        ev_new = sorted(set(ev_dir.iterdir()) - ev_before) if ev_dir.exists() else []
        manifest = records.manifest_summary(records.load_manifest(spec.dataset))
        record = {
            "schema_version": records.RECORD_SCHEMA_VERSION,
            "exp": spec.exp, "config": spec.config, "rep": rep, "label": spec.label,
            "kind": spec.kind, "dataset": spec.dataset, "params": spec.params, "job_args": list(spec.args),
            "status": status, "exit_code": exit_code, "error": error,
            "error_lines": _error_lines(log_text) if status != "ok" else [],
            "started_at": started, "ended_at": ended, "wall_seconds": wall,
            "command": cmd, "command_display": commands.to_display(cmd), "cwd": paths.rel_to_repo(cwd) or ".",
            "git": git, "host": records.host_info(),
            "workers_expected": spec.workers,
            "cluster_before": snap.as_record() if snap else None, "cluster_after": after,
            "seed": manifest["seed"], "dataset_skew": manifest["skew"],
            "raw_rows_manifest": manifest["rows_written"], "raw_rows_total_manifest": manifest["raw_rows_total"],
            "runner_options": {k: (str(v) if isinstance(v, Path) else v) for k, v in asdict(self.opts).items()
                               if k not in ("python",)},
            "metrics_path": paths.rel_to_repo(metrics_path), "log_path": paths.rel_to_repo(log_path),
            "event_logs": [paths.rel_to_repo(p) for p in ev_new],
            "archived_previous": [paths.rel_to_repo(p) for p in archived],
            "ivy": records.parse_ivy_times(log_text),
            "processing_seconds_total": (metrics or {}).get("processing_seconds_total"),
            "stage_seconds": (metrics or {}).get("stage_seconds"),
            "spark_version": (metrics or {}).get("spark_version"),
            "app_id": (metrics or {}).get("app_id"),
            "metrics": metrics,
        }
        records.write_record(rdir, record)
        return record

    def labels(self) -> list[str]:
        return sorted({s.label for s in self.specs if s.kind == "etl"})

    def cleanup(self, labels: Sequence[str] | None = None) -> None:
        """Delete curated/<label> and quarantine/<label> of this experiment's ETL runs on MinIO."""
        for label in (self.labels() if labels is None else labels):
            if not label.startswith(f"{self.exp}_"):
                raise ValueError(f"label {label!r} does not belong to experiment {self.exp}")
            for area in ("curated", "quarantine"):
                cmd = commands.minio_remove(self.opts.bucket, f"{area}/{label}")
                self.log(f"cleanup: {commands.to_display(cmd)}")
                if not self.opts.dry_run:
                    res = subprocess.run(cmd, cwd=paths.INFRA_DIR, capture_output=True, text=True)
                    if res.returncode != 0:
                        self.log(f"cleanup failed for {area}/{label}: {res.stderr.strip() or res.stdout.strip()}")

    def _dry_run(self) -> int:
        self._out(f"# [{self.exp}] DRY RUN: {len(self.plan)} run(s), reps={self.opts.reps}, "
                  f"order={self.opts.order}; nothing is executed")
        workers = cluster.WorkerController(self.opts.master_url, log=lambda m: self._out(f"#   {m}"),
                                           dry_run=True)
        for spec, rep in self.plan:
            if spec.workers is not None:
                workers.ensure(spec.workers)
                self._out(f"#   check: exactly {spec.workers} ALIVE worker(s) at {self.opts.master_url}, "
                          "no running application")
            cmd, cwd = build_command(spec, rep, self.opts)
            self._out(f"# {spec.config} r{rep} (cwd={paths.rel_to_repo(cwd) or '.'})")
            self._out(commands.to_display(cmd))
        workers.restore()
        if self.opts.cleanup_curated:
            self.cleanup()
        return 0
