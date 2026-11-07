"""Host conditions recorded with every run: free RAM and containers that do not belong to the project."""
from __future__ import annotations

import ctypes
import subprocess
import sys

from . import commands

PROJECT = "bigdata"  # `name:` in infra/docker-compose.yml


def memory_status() -> dict:
    """Total and available physical RAM in bytes (Windows GlobalMemoryStatusEx; /proc/meminfo on Linux)."""
    if sys.platform == "win32":
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(MemoryStatusEx)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return {"total_bytes": int(status.ullTotalPhys), "available_bytes": int(status.ullAvailPhys),
                    "memory_load_pct": int(status.dwMemoryLoad), "method": "GlobalMemoryStatusEx"}
        return {"method": "unavailable"}
    try:
        info = {}
        with open("/proc/meminfo", encoding="ascii") as fh:
            for line in fh:
                key, value = line.split(":", 1)
                info[key] = int(value.split()[0]) * 1024
        return {"total_bytes": info.get("MemTotal"), "available_bytes": info.get("MemAvailable"),
                "method": "/proc/meminfo"}
    except OSError:
        return {"method": "unavailable"}


def parse_containers(text: str, project: str = PROJECT) -> list[str]:
    """Names of running containers whose compose project is not `project` (lines: name<TAB>project)."""
    foreign = []
    for line in text.splitlines():
        if not line.strip():
            continue
        name, _, proj = line.partition("\t")
        if proj.strip() != project:
            foreign.append(name.strip())
    return sorted(foreign)


def foreign_containers() -> list[str] | None:
    """Running containers outside the project (other workloads competing for the 6 GB WSL VM); None if unknown."""
    try:
        res = subprocess.run(commands.running_containers(), capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return parse_containers(res.stdout) if res.returncode == 0 else None


def snapshot(with_containers: bool = True) -> dict:
    """Memory status plus (optionally) the foreign containers, for the run record."""
    out = {"memory": memory_status()}
    if with_containers:
        out["foreign_containers"] = foreign_containers()
    return out
