import os
import sys
import logging
import shlex
import subprocess
import textwrap
import yaml
import argparse
from pathlib import Path
     
from app.worker_manager import WorkerManager

def _run_shell(cmd: str, env: dict, cwd: Path):
    cmd = textwrap.dedent(cmd).strip()
    if not cmd:
        return
    logging.info("  ↳ %s", cmd)
    subprocess.check_call(shlex.split(cmd), cwd=cwd, env=env)

def _expand_env(d: dict) -> dict:
    return {k: os.path.expandvars(str(v)) for k, v in d.items()}

def worker_register(yaml_file: Path) -> None:
    if not yaml_file.exists():
        logging.error("Config file '%s' not found!", yaml_file)
        sys.exit(1)

    with yaml_file.open() as f:
        cfg = yaml.safe_load(f) or {}


    if not isinstance(cfg, dict):
        logging.error("YAML format error")
        sys.exit(1)
    

    tools_config = yaml_file.parent.resolve()
    for tool_name, spec in cfg.items():
        if not isinstance(spec, dict):
            logging.error("Tool '%s' must be a mapping", tool_name)
            sys.exit(1)

        logging.info("=== initializing %s ===", tool_name)

        env_add = _expand_env(spec.get("env", {}))
        env = os.environ.copy()
        env.update(env_add)

        setup_cmds = spec.get("setup", [])

        try:
            for cmd in setup_cmds:
                _run_shell(cmd, env, tools_config)
        except subprocess.CalledProcessError as e:
            logging.error("Tool %s setup failed: %s", tool_name, e)
            sys.exit(1)

        logging.info("%s ready ✔️", tool_name)
    
logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Start WorkerManager with optional YAML config"
    )   
     
    parser.add_argument(
        "-c", "--config",
        metavar="YAML_FILE",
        type=Path,
        help="Path to YAML config file"
    )

    args = parser.parse_args()

    if args.config:
        worker_register(args.config.resolve())

    work_manager = WorkerManager()
    work_manager.run()
