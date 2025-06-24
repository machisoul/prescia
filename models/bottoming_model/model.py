import os
import csv
import datetime
import yaml
import logging

class StockHistory:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        self.stock_symbol = None
        self.history_data_list = self.load_history_data()

    def load_history_data(self):
        self.stock_symbol = os.path.splitext(os.path.basename(self.csv_file_path))[0]
        history_data = []
        with open(self.csv_file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                daily_data_dict = {}
                for key, value in row.items():
                    try:
                        daily_data_dict[key] = float(value)
                    except ValueError:
                        daily_data_dict[key] = value
                history_data.append(daily_data_dict)
        return history_data

class BottomingModel:
    def __init__(self, databases, config):
        self.databases = databases
        self.config = config
        self.total = 0
        self.success_rate = 0
        self.average_final_change_rate = 0
        self.worst_decline_rate = 0
        self.mathematic_expectation = 0
        self.last_day_satisfied_stocks = []
        self.last_2week_satisfied_stocks = []
        # 支持周期配置
        self.period = config.get('period', 'day')
        self.min_decline_days = config.get('min_decline_days', 5)
        self.max_decline_days = config.get('max_decline_days', 10)
        self.min_total_decline_rate = config.get('min_total_decline_rate', 0.20)
        self.wait_days = config.get('wait_days', 20)
        self.payback_rate = config.get('payback_rate', 0.05)
        self.success_profit = config.get('success_profit', 0.045)
        self.min_close = config.get('min_close', 1.5)

    def is_condition_met(self, decline_days, total_decline_rate, open_price, close, turnoverrate, last_close, turnoverrate_diff):
        return (
            decline_days >= self.min_decline_days and
            decline_days <= self.max_decline_days and
            total_decline_rate > self.min_total_decline_rate and
            close > open_price
        )

    def calculate(self):
        number_of_successes = 0
        number_of_failures = 0
        total_change_rate = 0

        for filename in os.listdir(self.databases):
            decline_days = 0
            price_at_start_of_decline = 0
            turnoverrate_at_start_of_decline = 0
            max_turnoverrate_at_start_of_decline = 0
            turnoverrate_diff = 0
            total_decline_rate = 0

            isWrongStockSymbol = filename.startswith("SZ30") or filename.startswith("SH688") or filename.startswith("BJ")
            if isWrongStockSymbol or (not filename.endswith(".csv")):
                continue

            csv_file_path = os.path.join(self.databases, filename)
            stockHistory = StockHistory(csv_file_path)
            history_data = stockHistory.history_data_list

            for index, item in enumerate(history_data):
                if index < 1:
                    continue

                # 连续下跌天数
                if (item["close"] <= history_data[index - 1]["close"]) and (item["close"] < item["open"]):
                    decline_days += 1
                    if max_turnoverrate_at_start_of_decline < item["turnoverrate"]:
                        max_turnoverrate_at_start_of_decline = item["turnoverrate"]
                    if(decline_days == 1):
                        price_at_start_of_decline = history_data[index - 1]["close"]
                        turnoverrate_at_start_of_decline = item["turnoverrate"]
                    elif decline_days > 1:
                        total_decline_rate = ((price_at_start_of_decline - item["close"]) / price_at_start_of_decline)
                        turnoverrate_diff = item["turnoverrate"] - turnoverrate_at_start_of_decline
                    continue

                if (item["turnoverrate"] > max_turnoverrate_at_start_of_decline) and (item["close"] > self.min_close) and self.is_condition_met(decline_days, total_decline_rate, item["open"], item["close"], item["turnoverrate"], history_data[index - 1]["close"], turnoverrate_diff):
                    if (index == len(history_data) - 1):
                        self.last_day_satisfied_stocks.append(stockHistory.stock_symbol)
                        self.last_2week_satisfied_stocks.append(stockHistory.stock_symbol)
                        decline_days = 0
                        continue
                    elif (index > len(history_data) - 11):
                        self.last_2week_satisfied_stocks.append(stockHistory.stock_symbol)

                    self.total += 1
                    wait_days = self.wait_days
                    end_index = index + 1
                    if len(history_data) - index > wait_days:
                        end_index = index + wait_days
                    else:
                        end_index = len(history_data)

                    utc_time = datetime.datetime.utcfromtimestamp(float(item["timestamp"])/1000 + 86400).strftime("%Y-%m-%d %H:%M:%S.%f")
                    current_price = item["close"]
                    logging.info(f"{stockHistory.stock_symbol}, {current_price}: {utc_time}")

                    for i in range(index + 1, end_index):
                        if (history_data[i]["high"] > item["close"]) and ((history_data[i]["high"] - item["close"]) / item["close"] > self.payback_rate):
                            number_of_successes += 1
                            next_utc_time = datetime.datetime.utcfromtimestamp(float(history_data[i]["timestamp"])/1000 + 86400).strftime("%Y-%m-%d %H:%M:%S.%f")
                            logging.info(f"has been payback! {stockHistory.stock_symbol}: {next_utc_time}")
                            break
                        elif (i == end_index - 1):
                            number_of_failures += 1
                            next_utc_time = datetime.datetime.utcfromtimestamp(float(history_data[i]["timestamp"])/1000 + 86400).strftime("%Y-%m-%d %H:%M:%S.%f")
                            logging.info(f"has been drop! {stockHistory.stock_symbol}: {next_utc_time}")

                            current_final_change_rate = (history_data[i]["close"] - item["close"]) / item["close"]
                            total_change_rate += current_final_change_rate

                            self.average_final_change_rate = total_change_rate / number_of_failures

                            if current_final_change_rate < self.worst_decline_rate: 
                                self.worst_decline_rate = current_final_change_rate
                decline_days = 0
                max_turnoverrate_at_start_of_decline = 0

        if self.total > 0:
            self.success_rate = (number_of_successes / self.total)
            self.mathematic_expectation = ((number_of_successes / self.total) * self.success_profit + (number_of_failures / self.total) * self.average_final_change_rate)
            logging.info(f"Total: {self.total}")
            logging.info(f"Number of successes: {number_of_successes}, Number of failures: {number_of_failures}")
            logging.info("Mathematic Expectation: {:.2%}".format(self.mathematic_expectation))
            logging.info("Success Rate: {:.2%}".format(self.success_rate))
            logging.info("Failures rate: {:.2%}".format(number_of_failures / self.total))
            logging.info("Average change rate: {:.2%}".format(self.average_final_change_rate))
            logging.info("Worst decline rate: {:.2%}".format(self.worst_decline_rate))

def load_config(config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config
