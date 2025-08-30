#!/home/vidge/anaconda3/bin/python
import argparse
import logging
import os
import subprocess
import yaml
from models.bottoming_model.model import BottomingModel, load_config
from config import PresciaConfig, prescia_input

def setup_logging(log_file):
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 文件日志
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

def load_main_config(config_path="config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(
        description="Run stock bottoming or other models with configurable parameters."
    )
    parser.add_argument(
        "--log", type=str, default="models/bottoming_model/model.log",
        help="Log file path (default: models/bottoming_model/model.log)"
    )
    parser.add_argument(
        "--fetch-astock", action="store_true",
        help="Run astock history data script"
    )
    parser.add_argument(
        "--database", type=str,
        help="Database path"
    )
    parser.add_argument(
        "--model", type=str, default="bottoming",
        help="Model to run (default: bottoming)"
    )

    args = parser.parse_args()
    setup_logging(args.log)

    main_config = PresciaConfig

    # 使用 config.py 的配置
    db_path = prescia_input.get_database_path()
    model_conf = prescia_input.get_model_config()
    model_path = model_conf["model_path"]
    model_config_path = model_conf["model_config"]

    if args.fetch_astock:
        astock_script = main_config.astock_history_script
        astock_config = main_config.astock_config
        if not os.path.exists(astock_script):
            logging.error(f"astock script not found: {astock_script}")
            return
        if not os.path.exists(astock_config):
            logging.error(f"astock config not found: {astock_config}")
            return
        logging.info(f"Running astock script: {astock_script} with config: {astock_config}")
        subprocess.run(["python", astock_script], env={**os.environ, "CONFIG_PATH": astock_config})
        return

    config = load_config(model_config_path)
    if args.database:
        config["history"] = args.database

    if args.model.lower() == "bottoming":
        model = BottomingModel(config.get("history", "history"), config)
        model.calculate()
        logging.info(f"Last day satisfied: {model.last_day_satisfied_stocks}")
        logging.info(f"Last 2 week satisfied: {model.last_2week_satisfied_stocks}")
    else:
        logging.error(f"Model '{args.model}' is not supported.")

if __name__ == "__main__":
    main()