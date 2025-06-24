import argparse
import logging
import os
from models.bottoming_model.model import BottomingModel, load_config

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

def main():
    parser = argparse.ArgumentParser(
        description="Universal quant runner for stocks, bonds, crypto, futures, etc. Supports configurable models and parameters."
    )
    parser.add_argument(
        "--model", type=str, default="bottoming",
        help="Model to use (default: bottoming)"
    )
    parser.add_argument(
        "--config", type=str, default="models/bottoming_model/config.yaml",
        help="Path to model config.yaml (default: models/bottoming_model/config.yaml)"
    )
    parser.add_argument(
        "--database", type=str, default=None,
        help="Override database path in config"
    )
    parser.add_argument(
        "--log", type=str, default="models/bottoming_model/model.log",
        help="Log file path (default: models/bottoming_model/model.log)"
    )

    args = parser.parse_args()
    setup_logging(args.log)

    config = load_config(args.config)
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
