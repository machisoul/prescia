import os
import csv
import datetime

class StockHistoy:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        self.stock_symbol = None
        self.history_data_list = self.load_history_data()

    def load_history_data(self):
        self.stock_symbol = os.path.splitext(os.path.basename(self.csv_file_path))[0]
        # print(f"[INFO]: load {self.stock_symbol}")
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

        return  history_data
                

class ContinueDropModel:
    def __init__(self, databases):
        self.databases = databases
        self.total = 0
        self.success_rate = 0
        self.average_final_change_rate = 0
        self.worst_decline_rate = 0
        self.mathematic_expectation = 0
        self.last_day_satisfied_stocks = []
        self.last_2week_satisfied_stocks = []
    
    def is_condition_met(self, decline_days, total_decline_rate, open_price, close, turnoverrate, last_close, turnoverrate_diff):
        return (
            decline_days >= 5 and
            decline_days <= 10 and
            total_decline_rate > 0.20 and
            # close > open_price and
            close > open_price 
            # turnoverrate_diff > 0 //add more gailv
        )

    def calculate(self):
        #======= variables =======#
        number_of_successes = 0
        number_of_failures = 0
        total_change_rate = 0
        #======= variables =======#

        for filename in os.listdir(self.databases):
            #======= variables =======#
            decline_days = 0
            price_at_start_of_decline = 0
            turnoverrate_at_start_of_decline = 0
            max_turnoverrate_at_start_of_decline = 0
            turnoverrate_diff = 0
            total_decline_rate = 0
            #======= variables =======#

            isWrongStockSymbol = filename.startswith("SZ30") or filename.startswith("SH688") or filename.startswith("BJ")
            if isWrongStockSymbol or (not filename.endswith(".csv")):
                continue

            csv_file_path = os.path.join(self.databases, filename)
            stockHistoy = StockHistoy(csv_file_path)
            history_data = stockHistoy.history_data_list

            # if (len(history_data) >= 500):
            #     history_data = history_data[-500:]

            for index, item in enumerate(history_data):
                if index < 1:
                    continue

                # find continue down days
                if (item["close"] <= history_data[index - 1]["close"]) and (item["close"] < item["open"]):
                    decline_days += 1
                    if max_turnoverrate_at_start_of_decline < item["turnoverrate"]:
                        max_turnoverrate_at_start_of_decline = item["turnoverrate"]
                    
                    if(decline_days == 1):
                        price_at_start_of_decline = history_data[index - 1]["close"]
                        # price_at_start_of_decline = item["open"]
                        turnoverrate_at_start_of_decline = item["turnoverrate"]
                    elif decline_days > 1:
                        total_decline_rate = ((price_at_start_of_decline - item["close"]) / price_at_start_of_decline)
                        turnoverrate_diff = item["turnoverrate"] - turnoverrate_at_start_of_decline
                    continue

                # if (history_data[index - 1]["turnoverrate"] != 0) and ((item["turnoverrate"] - history_data[index - 1]["turnoverrate"]) / history_data[index - 1]["turnoverrate"] > 0.1) and (item["close"] > 3.0) and self.is_condition_met(decline_days, total_decline_rate, item["open"], item["close"], item["turnoverrate"], history_data[index - 1]["close"], turnoverrate_diff):
                # if self.is_condition_met(decline_days, total_decline_rate, item["open"], item["close"], item["turnoverrate"], history_data[index - 1]["close"], turnoverrate_diff):
                if (item["turnoverrate"] > max_turnoverrate_at_start_of_decline) and (item["close"] > 1.5) and self.is_condition_met(decline_days, total_decline_rate, item["open"], item["close"], item["turnoverrate"], history_data[index - 1]["close"], turnoverrate_diff):
                    if (index == len(history_data) - 1):
                        self.last_day_satisfied_stocks.append(stockHistoy.stock_symbol)
                        self.last_2week_satisfied_stocks.append(stockHistoy.stock_symbol)
                        decline_days = 0
                        continue
                    elif (index > len(history_data) - 11):
                        self.last_2week_satisfied_stocks.append(stockHistoy.stock_symbol)

                    self.total += 1
                    wait_days = 20
                    end_index = index + 1
                    if len(history_data) - index > wait_days:
                        end_index = index + wait_days
                    else:
                        end_index = len(history_data)

                    utc_time = datetime.datetime.utcfromtimestamp(float(item["timestamp"])/1000 + 86400).strftime("%Y-%m-%d %H:%M:%S.%f")
                    current_price = item["close"]
                    print(f"{stockHistoy.stock_symbol}, {current_price}: {utc_time}")
                    
                    for i in range(index + 1, end_index):
                        if (history_data[i]["high"] > item["close"]) and ((history_data[i]["high"] - item["close"]) / item["close"] > 0.05):
                            number_of_successes += 1
                            next_utc_time = datetime.datetime.utcfromtimestamp(float(history_data[i]["timestamp"])/1000 + 86400).strftime("%Y-%m-%d %H:%M:%S.%f")
                            print(f"has been payback! {stockHistoy.stock_symbol}: {next_utc_time}")
                            break
                        elif (i == end_index - 1):
                            number_of_failures += 1
                            next_utc_time = datetime.datetime.utcfromtimestamp(float(history_data[i]["timestamp"])/1000 + 86400).strftime("%Y-%m-%d %H:%M:%S.%f")
                            print(f"has been drop! {stockHistoy.stock_symbol}: {next_utc_time}")

                            current_final_change_rate = (history_data[i]["close"] - item["close"]) / item["close"]
                            total_change_rate += current_final_change_rate

                            self.average_final_change_rate = total_change_rate / number_of_failures

                            if current_final_change_rate < self.worst_decline_rate: 
                                self.worst_decline_rate = current_final_change_rate
                decline_days = 0
                max_turnoverrate_at_start_of_decline = 0


        if self.total > 0:
            self.success_rate = (number_of_successes / self.total)
            self.mathematic_expectation = ((number_of_successes / self.total) * 0.045 + (number_of_failures / self.total) * self.average_final_change_rate)
            print(f"Total: {self.total}")
            print(f"Number of successes: {number_of_successes}, Number of failures: {number_of_failures}")
            print("Mathematic Expectation: {:.2%}".format(self.mathematic_expectation))
            print("Success Rate: {:.2%}".format(self.success_rate))
            print("Failures rate: {:.2%}".format(number_of_failures / self.total))
            print("Average change rate: {:.2%}".format(self.average_final_change_rate))
            print("Worst decline rate: {:.2%}".format(self.worst_decline_rate))
                
    



continue_drop_model = ContinueDropModel("history")
continue_drop_model.calculate()
print(f"Last day satisfied: {continue_drop_model.last_day_satisfied_stocks}")
print(f"Last 2 week satisfied: {continue_drop_model.last_2week_satisfied_stocks}")