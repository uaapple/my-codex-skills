#!/usr/bin/env python3
"""Call Simulink Agentic Toolkit's evaluate_matlab_code over MCP stdio."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


SERVER = Path("/Users/guanzhengyang/.matlab/agentic-toolkits/bin/matlab-mcp-core-server")
EXTENSION = Path("/Users/guanzhengyang/.matlab/agentic-toolkits/simulink/tools/tools.json")


def send(proc: subprocess.Popen[str], msg: dict) -> None:
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
    proc.stdin.flush()


def read_json(proc: subprocess.Popen[str], timeout_s: float = 120.0) -> dict:
    assert proc.stdout is not None
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                err = ""
                try:
                    if proc.stderr is not None:
                        err = proc.stderr.read()
                except Exception:
                    err = ""
                raise RuntimeError(f"MCP server exited with code {proc.returncode}\n{err}")
            time.sleep(0.1)
            continue
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            print(line, file=sys.stderr)
    raise TimeoutError("Timed out waiting for MCP response")


def wait_for_id(proc: subprocess.Popen[str], msg_id: int, timeout_s: float = 180.0) -> dict:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        msg = read_json(proc, max(1.0, deadline - time.monotonic()))
        if msg.get("id") == msg_id:
            return msg
    raise TimeoutError(f"Timed out waiting for MCP response id={msg_id}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: satk_eval.py MATLAB_CODE_FILE", file=sys.stderr)
        return 2

    code = Path(sys.argv[1]).read_text(encoding="utf-8")
    proc = subprocess.Popen(
        [
            str(SERVER),
            "--matlab-session-mode=existing",
            f"--extension-file={EXTENSION}",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    try:
        send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "codex-satk-eval", "version": "0.1"},
                },
            },
        )
        init = wait_for_id(proc, 1, 120.0)
        if "error" in init:
            print(json.dumps(init, ensure_ascii=False, indent=2))
            return 1

        send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "evaluate_matlab_code",
                    "arguments": {"code": code},
                },
            },
        )
        result = wait_for_id(proc, 2, 600.0)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if "error" in result else 0
    finally:
        try:
            if proc.stdin:
                proc.stdin.close()
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
