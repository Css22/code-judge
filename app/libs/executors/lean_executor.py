import json
import tempfile
import io
import shlex
import subprocess, shutil, sys, textwrap
from pathlib import Path
from .executor import ScriptExecutor, ProcessExecuteResult, TIMEOUT_EXIT_CODE
from contextlib import contextmanager

# Add necessary extenstional libraries
PRE_TEMPLATE = f"""
import Mathlib
""".strip()


class LeanExecutor(ScriptExecutor):
    def __init__(self, run_cl: str, timeout: int = None, memory_limit: int = None,cpu_core: int = None):
        self.timeout = timeout
        self.memory_limit = (
            memory_limit + 128 * 1024 * 1024  # extra 128MB for python overhead
            if memory_limit
            else None
        )
        self.run_cl = run_cl
        self.cpu_core = cpu_core

    def setup_command(self, tmp_path: str, script: str):
        source_path = f"{tmp_path}/code.lean"
        with open(source_path, mode="w") as f:
            f.write(PRE_TEMPLATE)
            f.write("\n")
            f.write(script)
            f.flush()

        # generate the json file for REPL
        json_str = f'{{"path": "{source_path}", "allTactics": false}}'

        lean_cmd = shlex.split(
            self.run_cl.format(
                json=shlex.quote(json_str), workdir=shlex.quote(str(tmp_path))
            )
        )

        quota = int(round(self.cpu_core * 100))
        systemd_prefix = [
            "systemd-run",
            "--user",
            "--scope",
            "--quiet",
            "-p",
            f"CPUQuota={quota}%",
        ]

        cmd = systemd_prefix + lean_cmd
        yield cmd

    def process_result(self, result):
        try:
            if result.stderr and result.stderr.strip():
                return result

            stdout_text = (result.stdout or "").strip()

            if not stdout_text:
                # If stdout is empty, return an error result
                err_msg = "empty stdout from REPL"
                result.stderr = err_msg
                return result

            data = json.loads(stdout_text)

            sorries = data.get("sorries", [])
            messages = data.get("messages", []) or []

            errors = []
            for msg in messages:
                if msg.get("severity") == "error":
                    errors.append(msg)

            # If there are any errors or sorries, return false
            if len(sorries) > 0 or len(errors) > 0:
                result.stderr = result.stdout
                result.stdout = "fail"
            else:
                result.stdout = "pass"

        except Exception as e:
            result.stderr = f"Error processing result: {e}"
            return result

        return result
