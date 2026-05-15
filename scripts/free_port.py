"""释放指定 TCP 端口（Windows / 通用）。"""

from __future__ import annotations

import subprocess
import sys


def free_port(port: int) -> list[int]:
    killed: list[int] = []
    if sys.platform == "win32":
        out = subprocess.check_output(
            ["netstat", "-ano"],
            text=True,
            errors="replace",
        )
        pids: set[int] = set()
        needle = f":{port}"
        for line in out.splitlines():
            if needle not in line or "LISTENING" not in line.upper():
                continue
            parts = line.split()
            if not parts:
                continue
            try:
                pids.add(int(parts[-1]))
            except ValueError:
                continue
        for pid in pids:
            r = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                text=True,
            )
            if r.returncode == 0:
                killed.append(pid)
    else:
        out = subprocess.check_output(
            ["lsof", "-ti", f":{port}"],
            text=True,
            errors="replace",
        )
        for line in out.split():
            line = line.strip()
            if not line.isdigit():
                continue
            pid = int(line)
            subprocess.run(["kill", "-9", str(pid)], check=False)
            killed.append(pid)
    return killed


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    killed = free_port(port)
    if killed:
        print(f"已结束占用端口 {port} 的进程: {', '.join(map(str, killed))}")
    else:
        print(f"端口 {port} 未被占用")


if __name__ == "__main__":
    main()
