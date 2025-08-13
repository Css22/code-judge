import json
import os
import subprocess
import hashlib
from pathlib import Path
from typing import Any, Dict
import logging

import yaml

LOG_PREFIX = "[bootstrap]"


def read_yaml(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    except Exception as e:
        raise ValueError(f"can not read yaml file {path}: {e}")

    return data


def hash_dict(d: Dict[str, Any]) -> str:
    # Serialized hash as fingerprint
    payload = json.dumps(d, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_state(state_file: Path) -> Dict[str, Any]:
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_state(state_file: Path, state: Dict[str, Any]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def exec_shell(cmd: str, env: Dict[str, str], cwd: Path) -> None:
    bash = os.environ.get("SHELL", "/bin/bash")
    full = [bash, "-lc", cmd]
    completed = subprocess.run(full, cwd=str(cwd), env=env)
    if completed.returncode != 0:
        raise RuntimeError(
            f"failed to execute command: {cmd} (exit={completed.returncode})"
        )


def run_step(step: Dict[str, Any], env: Dict[str, str], workdir: Path) -> None:
    stype = step.get("type")
    name = step.get("name") or stype
    logging.info(f"{LOG_PREFIX} ▶ {name}")

    if stype == "shell":
        script = step.get("run", "")
        exec_shell(script, env, workdir)
    else:
        raise ValueError(f"unknow: {stype}")


def bootstrap_workers_from_yaml(yaml_path: str, state_file: str = ".state/state.json") -> None:
    # yaml_path is the path to the YAML configuration file and used to initialize workers.
    # state_file is the path to the state file and used to avoid repeated initialization.
    yaml_path = Path(yaml_path)
    state_file = Path(state_file)

    if not yaml_path.exists():
        raise FileNotFoundError(f"not yaml file: {yaml_path}")

    cfg = read_yaml(yaml_path)
    tools = cfg.get("tools") or {}

    state = load_state(state_file)

    workdir = Path.cwd()

    for name, node in tools.items():
        logging.info(f"{LOG_PREFIX} initializing {name} ...")
        steps = node.get("setup", []) or []
        ex_env = os.environ.copy()

        # Fingerprint: related to the env + steps of the executor
        sig = hash_dict({"setup": steps})
        saved = state.get(name, {})
        applied_sig = saved.get("applied_sig")

        if applied_sig == sig:
            # use fingerprint to avoid repeated initialization
            logging.info(
                f"{LOG_PREFIX} tool {name} has already been initialized and configuration is unchanged, skipping."
            )
            continue

        logging.info(f"{LOG_PREFIX} Initialize tool {name} …")
        for step in steps:
            run_step(step, ex_env, workdir)

        # update state
        state[name] = {"applied_sig": sig}
        save_state(state_file, state)
    logging.info("finish initialization")
