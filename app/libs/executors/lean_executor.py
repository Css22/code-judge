from contextlib import contextmanager
import tempfile
import io
import shlex
import subprocess, shutil, sys, textwrap
from pathlib import Path
from .executor import ScriptExecutor, ProcessExecuteResult, TIMEOUT_EXIT_CODE

# Add necessary extenstional libraries
EXTRA_TOML = """
[[require]]
name  = "mathlib"
scope = "leanprover-community"
"""

PRE_TEMPLATE = f"""
import Mathlib
""".strip()

# Avoid import error
POST_TEMPLATE = f"""
def hello := "world"
""".strip()
class LeanExecutor(ScriptExecutor):
    def __init__(self, run_cl: str, timeout: int = None, memory_limit: int = None, cpu_core: int = None):
        self.timeout = timeout
        self.memory_limit = (
            memory_limit + 128 * 1024 * 1024  # extra 128MB for python overhead
            if memory_limit
            else None
        )
        self.run_cl = run_cl
        self.cpu_core = cpu_core
    
    def lean_initialization(self, tmp_path: str):
        # lean initialization
        root = Path(tmp_path)
        init_command = ['lake', 'init', 'LeanCode']

        result = subprocess.run(init_command, cwd=root, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Failed to initialize Lean project: {result.stderr}")

    def setup_command(self, tmp_path: str, script: str):
        
        self.lean_initialization(tmp_path)
        toml_file  = f'{tmp_path}/lakefile.toml'
        with open(toml_file, 'a') as f:
            f.write(EXTRA_TOML)
            f.flush()
            
        source_path = f"{tmp_path}/LeanCode/Basic.lean"
        with open(source_path, mode='w') as f:
            f.write(PRE_TEMPLATE.format(timeout=self.timeout, memory_limit=self.memory_limit, cpu_core=self.cpu_core))
            f.write("\n")
            f.write(script)
            f.write("\n")
            f.write(POST_TEMPLATE)
            f.flush()

        lean_cmd = shlex.split(self.run_cl)      

        quota = int(round(self.cpu_core * 100))
        systemd_prefix = [
            "systemd-run", "--user", "--scope", "--quiet",
            "-p", f"CPUQuota={quota}%"
        ]

        cmd = systemd_prefix + lean_cmd
        yield cmd

    def process_result(self, result):
        # if SCRIPT_ENDING_MARK in result.stdout:
        #     result.stdout, meta_info = result.stdout.split(SCRIPT_ENDING_MARK, 2)
        #     for line in io.StringIO(meta_info):
        #         if line.startswith(DURATION_MARK):
        #             result.cost = float(line[len(DURATION_MARK):])
        #             break
        print(result)
        return result
