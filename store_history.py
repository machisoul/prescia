print("文件已开始执行")
import requests
import time
import os
import math
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
print("import finished")


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

def getAllStock(headers, base_filter_url, each_page_size):
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
                if 'ST' not in item['name']:
                    all_stock_symbol[item['symbol']] = item['name']
        except Exception as e:
            print(f"第{i}页请求出错:", e)

    print(f"Fetched {len(all_stock_symbol)} stock symbols.")
    return all_stock_symbol

def fetch_stock_data(stock_symbol, base_history_url, headers, delta_days_str, history_dir):
    print(stock_symbol)
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

def storeAllStockHistory(headers, base_history_url, all_stock_symbol, target_path):
    print("Storing all stock history data...")
    history_dir = target_path
    log_file = 'store.log'
    last_time = None
    delta_days = 500

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

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [
            executor.submit(fetch_stock_data, stock_symbol, base_history_url, headers, delta_days_str, history_dir)
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
  # begin: ====================================
  headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
              "Cookie": "cookiesu=471750730673586; Hm_lvt_1db88642e346389874251b5a1eded6e3=1750730675; HMACCOUNT=C62EE38431C5EE0F; device_id=803df54fcf822d42e9491a868dce5ffb; remember=1; xq_a_token=dc69165b441230e5ed5a19eb64d8a1b79c21ec0e; xqat=dc69165b441230e5ed5a19eb64d8a1b79c21ec0e; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjE5MTExOTE4MDEsImlzcyI6InVjIiwiZXhwIjoxNzUzMzIyNjk5LCJjdG0iOjE3NTA3MzA2OTkyMjQsImNpZCI6ImQ5ZDBuNEFadXAifQ.kgerdQP1xFNmiQNqCasNAzoqm84rFvNcLHmULoi1rabn1R3RrwtsCBxhd7coYsfVKPtNe6MYgIo-bp1gAoW3th7yUdyw8QYrAEDGldaeLPryTFdbTnwBg0Nf9_dtGGahL3oZPL3tdLr_KhYQIvh1OowOPvwJb3On5GnDGWn8C0IqrmnESeou9RAOxwCV06bgL7kCcRUkHiu4O_b-gjKPi8qXNKul9rNMSiR-uro05tWztZrh1sqs7PypvSLxma_7NwRdQ0HW4Mq0M6AYbH-6xm3jEPbWbT6OV9BxUPSPkiaWiYXUj39tByzjDnVtc_OwFNOmvbuHE4Lm2kUyV6ci0g; xq_r_token=e6c466f8974ffe56a8d71430a662572f6625ee31; xq_is_login=1; u=1911191801; is_overseas=0; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1750730745; ssxmod_itna=eqRxyD07D=G=TqWqYj+hDQk43qxYqD5D2Dl4BU=rGglDFqAPDODCx7IgKNRxwYpSsGDFwW=qMD0yGYm9D06HDf40Wmz6De+1=beOgDp2UQGWQe7aUQIRuK7HqeRPqDqf24mIrTNR+RmDGoDbuoDfqDlDDmq6qGXUkdbDYYDC4GwDeG+beDWAeDLDYoDY3WoTeGhDB=DmqDB814DATia14DFbeWb==rDm4DfDDLepCxeiKGHDD3Wq1wmv8fQwoHDzRcv0Q2PIo+OiDGWiRbaaPGuDG6=bQWvD7jOSCybN1cHwpFkqXQl+2N6ApYAm8QDiiGwaqYaw7BPUiGj0eBGDieh8ex4ehKjqtbK6jj+Ap7lvgj2RhUcctB=qbD+/heK4IcnGB0eXADmOGxYR1nwsAGPexh7T4iGM7GKtbrbDxD; ssxmod_itna2=eqRxyD07D=G=TqWqYj+hDQk43qxYqD5D2Dl4BU=rGglDFqAPDODCx7IgKNRxwYpSsGDFwW=qmDDPE7Gii4WmPDFhD4EQrDGN4cm9DeaqO5GYKcU=YedLaLqf2QMLPrQTzGnx2CYXfWOGr04Rh5z0au7b=PCOcpxb2YOg6B827aQKU9kgpoh34EFXQihIaq+Re2aGauDRPTHI4g8AzcWdeSLgrGjZxoAZ8PwR7F06/b=EKlEMoa0utiRizSWUoxkVaS8FoqXI1lXzvZc+3px2i+Nf6wRI6DxEIUIK4v+XMcgYD=WwcnrBT+Tt5NlhxD4q+Gi+DDHBD9xDPD"
  }

  base_filter_url = (
      "https://xueqiu.com/service/screener/screen?"
      "category=CN&exchange=sh_sz&areacode=&indcode=&order_by=symbol&order=desc&page=[fill]&size=[fill]&only_count=0&"
      "current=&pct=&mc=&volume="
      "&_=[fill]"
      )

  all_stock = getAllStock(headers, base_filter_url, 30)

  # with open('stock_symbols.txt', 'w') as f:
  #     for symbol, name in all_stock.items():
  #         f.write(f"{symbol}: {name}\n")
  # exit()

  base_history_url = (
      "https://stock.xueqiu.com/v5/stock/chart/kline.json?"
      "symbol=[fill]&begin=[fill]&"
      "period=day&type=before&count=[fill]&indicator=kline,pe,pb,ps,pcf,market_capital,agt,ggt,balance"
      )
  storeAllStockHistory(headers, base_history_url, all_stock, "history")


if __name__ == "__main__":
    main()
    print("All stock history data has been stored successfully.")