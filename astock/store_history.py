import requests
import time
import os
import math
import csv
import yaml
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class FilterURL:
    def __init__(self, base_url, *args, **kwargs):
        self.base_url = base_url
        self.params = kwargs
        self.url = self.build_url()

    def build_url(self):
        filled_url = self.base_url
        for key, value in self.params.items():
            filled_url = filled_url.replace("[fill]", f"{value}", 1)
        return filled_url

def load_config():
    with open('astock/config.yaml', 'r') as f:
        return yaml.safe_load(f)

def getAllStock(config):
    headers = config['headers']
    base_filter_url = config['urls']['base_filter']
    each_page_size = config['settings']['page_size']
    exclude_names = config['stock_filter']['exclude_names']

    filter_url_first_page = FilterURL(base_filter_url, page="1", size=str(each_page_size), current_unix_time=str(int(time.time() * 1000)))

    print(f"Fetching stock symbols from: {filter_url_first_page.url}")
    try:
        resp = requests.get(url=filter_url_first_page.url, headers=headers, timeout=10)
        print("响应内容:", resp.text)
        resp.raise_for_status()
        count_value = resp.json()['data']['count']
    except Exception as e:
        print("请求出错:", e)
        return {}

    # get the number of pages
    print(f"Total stock count: {count_value}")
    count_value = resp.json()['data']['count']
    number_of_pages = math.ceil(count_value / each_page_size)

    all_stock_symbol = {}
    for i in range(1, number_of_pages + 1):
        filter_url_current_page = FilterURL(
            base_filter_url, page=str(i), size=str(each_page_size), current_unix_time=str(int(time.time() * 1000))
        )
        try:
            print(f"请求第{i}页: {filter_url_current_page.url}")
            resp = requests.get(url=filter_url_current_page.url, headers=headers, timeout=10)
            print(f"第{i}页响应: {resp.text[:200]}")  # 只打印前200字符，防止太长
            data_list = resp.json().get('data', {}).get('list', [])
            for item in data_list:
                if not any(excluded in item['name'] for excluded in exclude_names):
                    all_stock_symbol[item['symbol']] = item['name']
        except Exception as e:
            print(f"第{i}页请求出错:", e)

    print(f"Fetched {len(all_stock_symbol)} stock symbols.")
    return all_stock_symbol

def fetch_stock_data(stock_symbol, config, delta_days_str, history_dir):
    headers = config['headers']
    base_history_url = config['urls']['base_history']
    history_url = FilterURL(base_history_url, symbol=stock_symbol, current_unix_time=str(int(time.time() * 1000)), count=delta_days_str)
    
    session = requests.Session()
    session.get("https://xueqiu.com/", headers=headers)
    res = session.get(url=history_url.url, headers=headers)
    response_json = res.json()
    
    columns = response_json['data']['column']
    items = response_json['data']['item']
    
    csv_file_name = f"{stock_symbol}.csv"
    csv_file_path = os.path.join(history_dir, csv_file_name)
    file_exists = os.path.exists(csv_file_path)
    
    with open(csv_file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(columns)
        for item in items:
            writer.writerow(item)

def storeAllStockHistory(config, all_stock_symbol):
    settings = config['settings']
    history_dir = settings['history_dir']
    log_file = settings['log_file']
    delta_days = settings['delta_days']
    max_workers = settings['max_workers']

    print("Storing all stock history data...")
    log_file = 'store.log'
    last_time = None

    if not os.path.exists(history_dir):
        os.makedirs(history_dir)

    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            f.write('') 
        last_time = None
    else:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1]
                last_time_str = last_line.split('up to ')[1].split(',')[0].strip()
                last_time = datetime.strptime(last_time_str, '%Y-%m-%d')
            # else:
            #     last_time = None

    current_time = datetime.now()
    # if last_time:
    #     delta_days = (current_time - last_time).days

    delta_days_str = None
    if delta_days > 0:
        delta_days_str = f"-{delta_days}"
    else:
        exit()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch_stock_data, stock_symbol, config, delta_days_str, history_dir)
            for stock_symbol in all_stock_symbol.keys()
        ]
        
        for future in as_completed(futures):
            try:
                future.result()  # This will raise any exceptions caught during the thread execution
            except Exception as e:
                print(f"Exception occurred: {e}")

    ## store log:
    formatted_time = current_time.strftime('%Y-%m-%d')
    new_log_entry = f"Already stored data up to {formatted_time}, unixTime: {current_time}\n"
    with open(log_file, 'a') as f:
        f.write(new_log_entry)


def main():
    print("Starting to store all stock history data...")
    config = load_config()
    
    all_stock = getAllStock(config)
    storeAllStockHistory(config, all_stock)

if __name__ == "__main__":
    main()
    print("All stock history data has been stored successfully.")