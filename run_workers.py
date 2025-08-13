import argparse
import logging

from app.worker_bootstrap import bootstrap_workers_from_yaml
from app.worker_manager import WorkerManager


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bootstrap workers from YAML configuration."
    )
    parser.add_argument(
        "-c",
        "--config_yaml_path",
        type=str,
        default="config.yaml",
        help="the path to the config yaml file",
    )

    args = parser.parse_args()
    config_yaml_path = args.config_yaml_path

    logging.info(f"Initializing workers from {config_yaml_path} ...")
    bootstrap_workers_from_yaml(config_yaml_path)
    logging.info("Workers initialized successfully.")
    work_manager = WorkerManager()
    work_manager.run()
