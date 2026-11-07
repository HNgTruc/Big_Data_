"""Spark standalone cluster state (master JSON) and worker stop/start for scale_workers."""
from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Callable

from . import commands, paths

WORKER_2_SERVICE = "spark-worker-2"


class ClusterStateError(RuntimeError):
    """The cluster is not in the state an experiment run requires; the runner must stop."""


@dataclass
class ClusterSnapshot:
    """What the master reports: ALIVE workers, their cores, running apps."""
    alive_workers: int
    total_alive_cores: int
    workers: list[dict]
    active_apps: int
    status: str

    def as_record(self) -> dict:
        """Plain dict for the run record."""
        return {"alive_workers": self.alive_workers, "total_alive_cores": self.total_alive_cores,
                "active_apps": self.active_apps, "master_status": self.status,
                "workers": self.workers}


def parse_master_json(data: dict) -> ClusterSnapshot:
    """Summarise the master's /json/ answer. Only workers with state == ALIVE count.

    A stopped worker may stay listed as DEAD for a while, so the list length is not used.
    """
    alive = [w for w in data.get("workers", []) if w.get("state") == "ALIVE"]
    return ClusterSnapshot(
        alive_workers=len(alive),
        total_alive_cores=sum(int(w.get("cores", 0)) for w in alive),
        workers=[{"id": w.get("id"), "host": w.get("host"), "cores": w.get("cores"),
                  "memory_mb": w.get("memory"), "state": w.get("state")} for w in data.get("workers", [])],
        active_apps=len(data.get("activeapps", [])),
        status=str(data.get("status")),
    )


def fetch_snapshot(url: str, timeout: float = 5.0) -> ClusterSnapshot:
    """Read the master's /json/ endpoint; ClusterStateError if it does not answer."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return parse_master_json(json.loads(resp.read().decode("utf-8")))
    except (OSError, ValueError) as exc:
        raise ClusterStateError(f"cannot read Spark master JSON at {url}: {exc}") from exc


def check_expected(snap: ClusterSnapshot, workers: int, cores_per_worker: int | None) -> None:
    """Raise ClusterStateError unless exactly `workers` are ALIVE with the expected cores."""
    if snap.alive_workers != workers:
        raise ClusterStateError(f"expected {workers} ALIVE worker(s), master reports {snap.alive_workers}")
    if cores_per_worker is not None and snap.total_alive_cores != workers * cores_per_worker:
        raise ClusterStateError(f"expected {workers * cores_per_worker} cores on ALIVE workers, "
                                f"master reports {snap.total_alive_cores}")
    if snap.active_apps:
        raise ClusterStateError(f"{snap.active_apps} application(s) still running on the cluster")


def wait_for(url: str, predicate: Callable[[ClusterSnapshot], bool], what: str,
             timeout_s: float = 180.0, poll_s: float = 3.0, stable_polls: int = 2) -> ClusterSnapshot:
    """Poll the master until `predicate` holds on `stable_polls` consecutive snapshots."""
    deadline = time.monotonic() + timeout_s
    streak, snap = 0, None
    while time.monotonic() < deadline:
        try:
            snap = fetch_snapshot(url)
            streak = streak + 1 if predicate(snap) else 0
        except ClusterStateError:
            streak = 0
        if streak >= stable_polls:
            return snap
        time.sleep(poll_s)
    last = snap.as_record() if snap else "no answer"
    raise ClusterStateError(f"timed out after {timeout_s:.0f}s waiting for {what}; last state: {last}")


def wait_alive(url: str, workers: int, timeout_s: float = 180.0) -> ClusterSnapshot:
    """Wait until exactly `workers` workers are ALIVE (two stable polls)."""
    return wait_for(url, lambda s: s.alive_workers == workers, f"{workers} ALIVE worker(s)", timeout_s)


def wait_idle(url: str, timeout_s: float = 60.0) -> ClusterSnapshot:
    """The previous driver container is gone, but the master may need a moment to drop the app."""
    return wait_for(url, lambda s: s.active_apps == 0, "no running application", timeout_s, stable_polls=1)


@dataclass
class WorkerController:
    """Stops/starts spark-worker-2 for single-worker runs and remembers whether it did.

    Only transitions this object caused are undone; an unexpected worker count is an error,
    never "fixed" silently.
    """

    master_url: str
    log: Callable[[str], None] = print
    dry_run: bool = False
    stopped_worker_2: bool = False
    actions: list[str] = field(default_factory=list)

    def _compose(self, action: str) -> None:
        cmd = commands.compose_service(action, WORKER_2_SERVICE)
        self.log(f"$ {commands.to_display(cmd)}  (cwd=infra)")
        self.actions.append(action)
        if self.dry_run:
            return
        res = subprocess.run(cmd, cwd=paths.INFRA_DIR, capture_output=True, text=True)
        if res.returncode != 0:
            raise ClusterStateError(f"`docker compose {action} {WORKER_2_SERVICE}` failed: "
                                    f"{res.stderr.strip() or res.stdout.strip()}")

    def ensure(self, workers: int) -> None:
        """Bring the cluster to `workers` ALIVE workers (1 or 2) if this controller may do so."""
        if workers not in (1, 2):
            raise ValueError("only 1 or 2 workers are supported by this cluster")
        if self.dry_run:
            if workers == 1 and not self.stopped_worker_2:
                self.stopped_worker_2 = True
                self._compose("stop")
            elif workers == 2 and self.stopped_worker_2:
                self.stopped_worker_2 = False
                self._compose("start")
            return
        if workers == 1 and not self.stopped_worker_2:
            snap = fetch_snapshot(self.master_url)
            if snap.alive_workers != 2:
                raise ClusterStateError(f"before stopping {WORKER_2_SERVICE}: expected 2 ALIVE workers, "
                                        f"found {snap.alive_workers}")
            # Set first: if `stop` fails half-way, restore() in the runner's finally still starts the worker.
            self.stopped_worker_2 = True
            self._compose("stop")
            wait_alive(self.master_url, 1)
            self.log("master reports 1 ALIVE worker")
        elif workers == 2 and self.stopped_worker_2:
            self.restore()

    def restore(self) -> None:
        """Start spark-worker-2 again (if this controller stopped it) and wait for 2 ALIVE workers."""
        if not self.stopped_worker_2:
            return
        self._compose("start")  # `docker compose start` on a running service is harmless
        self.stopped_worker_2 = False
        if not self.dry_run:
            wait_alive(self.master_url, 2)
            self.log("master reports 2 ALIVE workers again")
