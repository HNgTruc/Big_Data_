"""Host and container paths shared by the experiment runners.

Host paths are absolute `Path`s; container paths are POSIX strings under the mount
point used in infra/docker-compose.yml (`../src`, `../data`, `../results` -> /opt/spark/work-dir/).
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[3]
INFRA_DIR = REPO_ROOT / "infra"
RAW_DIR = REPO_ROOT / "data" / "raw"
RESULTS_DIR = REPO_ROOT / "results"
CONTAINER_ROOT = PurePosixPath("/opt/spark/work-dir")

# Keys of infra/.env that the runners may read. Credentials are deliberately not listed.
ENV_KEYS = ("MINIO_BUCKET", "HADOOP_AWS_VERSION", "SPARK_MASTER_UI_PORT", "SPARK_WORKER_CORES")


def metrics_dir(exp: str) -> Path:
    """results/metrics/<exp>/ on the host."""
    return RESULTS_DIR / "metrics" / exp


def logs_dir(exp: str) -> Path:
    """results/logs/<exp>/ on the host."""
    return RESULTS_DIR / "logs" / exp


def figures_dir(exp: str) -> Path:
    """results/figures/<exp>/ on the host."""
    return RESULTS_DIR / "figures" / exp


def run_dir(exp: str, config: str, rep: int) -> Path:
    """Host folder holding the metrics JSON and run record of one repetition."""
    return metrics_dir(exp) / "runs" / config / f"r{rep}"


def to_container(host_path: Path) -> str:
    """Map a host path inside the repo to the path the Spark containers see."""
    rel = host_path.resolve().relative_to(REPO_ROOT)
    return str(CONTAINER_ROOT.joinpath(*rel.parts))


def rel_to_repo(path: Path) -> str:
    """Repo-relative POSIX path (portable inside run records)."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def read_env(path: Path | None = None) -> dict[str, str]:
    """Read the whitelisted, non-secret keys of infra/.env (missing file -> empty dict)."""
    path = path or INFRA_DIR / ".env"
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() in ENV_KEYS:
            out[key.strip()] = value.strip()
    return out
