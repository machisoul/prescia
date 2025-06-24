from filter_url import FilterURL
import requests
import time
import math
import time 
import datetime

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
            "Cookie": "cookiesu=471750730673586; Hm_lvt_1db88642e346389874251b5a1eded6e3=1750730675; HMACCOUNT=C62EE38431C5EE0F; device_id=803df54fcf822d42e9491a868dce5ffb; remember=1; xq_a_token=dc69165b441230e5ed5a19eb64d8a1b79c21ec0e; xqat=dc69165b441230e5ed5a19eb64d8a1b79c21ec0e; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjE5MTExOTE4MDEsImlzcyI6InVjIiwiZXhwIjoxNzUzMzIyNjk5LCJjdG0iOjE3NTA3MzA2OTkyMjQsImNpZCI6ImQ5ZDBuNEFadXAifQ.kgerdQP1xFNmiQNqCasNAzoqm84rFvNcLHmULoi1rabn1R3RrwtsCBxhd7coYsfVKPtNe6MYgIo-bp1gAoW3th7yUdyw8QYrAEDGldaeLPryTFdbTnwBg0Nf9_dtGGahL3oZPL3tdLr_KhYQIvh1OowOPvwJb3On5GnDGWn8C0IqrmnESeou9RAOxwCV06bgL7kCcRUkHiu4O_b-gjKPi8qXNKul9rNMSiR-uro05tWztZrh1sqs7PypvSLxma_7NwRdQ0HW4Mq0M6AYbH-6xm3jEPbWbT6OV9BxUPSPkiaWiYXUj39tByzjDnVtc_OwFNOmvbuHE4Lm2kUyV6ci0g; xq_r_token=e6c466f8974ffe56a8d71430a662572f6625ee31; xq_is_login=1; u=1911191801; is_overseas=0; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1750730745; ssxmod_itna=eqRxyD07D=G=TqWqYj+hDQk43qxYqD5D2Dl4BU=rGglDFqAPDODCx7IgKNRxwYpSsGDFwW=qMD0yGYm9D06HDf40Wmz6De+1=beOgDp2UQGWQe7aUQIRuK7HqeRPqDqf24mIrTNR+RmDGoDbuoDfqDlDDmq6qGXUkdbDYYDC4GwDeG+beDWAeDLDYoDY3WoTeGhDB=DmqDB814DATia14DFbeWb==rDm4DfDDLepCxeiKGHDD3Wq1wmv8fQwoHDzRcv0Q2PIo+OiDGWiRbaaPGuDG6=bQWvD7jOSCybN1cHwpFkqXQl+2N6ApYAm8QDiiGwaqYaw7BPUiGj0eBGDieh8ex4ehKjqtbK6jj+Ap7lvgj2RhUcctB=qbD+/heK4IcnGB0eXADmOGxYR1nwsAGPexh7T4iGM7GKtbrbDxD; ssxmod_itna2=eqRxyD07D=G=TqWqYj+hDQk43qxYqD5D2Dl4BU=rGglDFqAPDODCx7IgKNRxwYpSsGDFwW=qmDDPE7Gii4WmPDFhD4EQrDGN4cm9DeaqO5GYKcU=YedLaLqf2QMLPrQTzGnx2CYXfWOGr04Rh5z0au7b=PCOcpxb2YOg6B827aQKU9kgpoh34EFXQihIaq+Re2aGauDRPTHI4g8AzcWdeSLgrGjZxoAZ8PwR7F06/b=EKlEMoa0utiRizSWUoxkVaS8FoqXI1lXzvZc+3px2i+Nf6wRI6DxEIUIK4v+XMcgYD=WwcnrBT+Tt5NlhxD4q+Gi+DDHBD9xDPD"
}

base_filter_url = (
    "https://xueqiu.com/service/screener/screen?"
    "category=CN&exchange=sh_sz&areacode=&indcode=&order_by=symbol&order=desc&page=[fill]&size=[fill]&only_count=0&"
    "current=[fill]&pct=&tr=[fill]"
    "&_=[fill]"
    )

each_page_size = 30
current_price = "5_1000"
turnover = "0_100"
filter_url_first_page = FilterURL(base_filter_url, page="1", size=str(each_page_size), current=current_price, tr=turnover, current_unix_time=str(int(time.time() * 1000)))

# get the number of pages
resp = requests.get(url=filter_url_first_page.url, headers=headers)
count_value = resp.json()['data']['count']
number_of_pages = math.ceil(count_value / each_page_size)

all_stock_symbol = []
for i in range(1, number_of_pages + 1):
    filter_url_current_page = FilterURL(base_filter_url, page=str(i), size=str(each_page_size), current=current_price, tr=turnover, current_unix_time=str(int(time.time() * 1000)))
    resp = requests.get(url=filter_url_current_page.url, headers=headers)
    current_page_symbol_list = [item['symbol'] for item in resp.json()['data']['list']]
    all_stock_symbol.extend(current_page_symbol_list)

base_history_url = (
    "https://stock.xueqiu.com/v5/stock/chart/kline.json?"
    "symbol=[fill]&begin=[fill]&"
    "period=day&type=before&count=[fill]&indicator=kline,pe,pb,ps,pcf,market_capital,agt,ggt,balance"
    )
# print(all_stock_symbol)
all_count = 0
right_count = 0
all_drop = 0
drop_count = 0
worst_possible_drop = 0
average_drop = 0
continue_drop_count = 0
continue_drop_value = 0
first_drop_close_value = 0
right_stock = []

for stock_symbol in all_stock_symbol:
    if stock_symbol.startswith("SZ30") or stock_symbol.startswith("SH688") or stock_symbol.startswith("BJ"):
        continue
    history_url = FilterURL(base_history_url, symbol=stock_symbol, current_unix_time=str(int(time.time() * 1000)), count="-15")
    print(f"check {stock_symbol}")

    session = requests.Session()
    session.get("https://xueqiu.com/", headers = headers)
    # res = requests.get(url=history_url.url,headers = headers)
    res = session.get(url=history_url.url,headers = headers)

    items = res.json()['data']['item']

    first_close = 0
    second_hish = 0
    has_second_hish = False
    for index, item in enumerate(items):
        if index < 1:
            continue
        timestamp, volume, open_value, high, low, close, chg, percent, turnoverrate, *_ = item
        last_timestamp, last_volume, last_open_value, last_high, last_low, last_close, last_chg, last_percent, last_turnoverrate, *_ = items[index - 1]
        if (close <= last_close) and (close < open_value):
            continue_drop_count += 1
            if(continue_drop_count == 1):
                first_drop_close_value = last_close
            elif continue_drop_count > 1:
                continue_drop_value = ((first_drop_close_value - close) /  first_drop_close_value)
                # print("continue drop value: {:.2%}".format(continue_drop_value))
            continue
        # print(f"Current Item - Timestamp: {timestamp}, Open: {open_value}, High: {high}, Low: {low}, Close: {close}, chg: {chg}, percent: {percent}, turnoverrate: {turnoverrate}")
        # if(close < open_value) and ((open_value - close) / open_value > 0.09) and (high > last_low):
        # if True:
        if (continue_drop_count >= 4) and (close > last_close) and (close > open_value) and (turnoverrate > 2.0) and (continue_drop_value > 0.2):
            continue_drop_count = 0
            utc_time = datetime.datetime.utcfromtimestamp(float(timestamp)/1000 + 86400).strftime("%Y-%m-%d %H:%M:%S.%f")
            print(f"{stock_symbol}: {utc_time}")
            right_stock.append(stock_symbol)
            all_count = all_count + 1
            
            # wait_day = 20
            # end_index = index + 1
            # if len(items) - index > wait_day:
            #     end_index = index + wait_day
            # elif len(items) - index <= wait_day:
            #     end_index = len(items)
            # for i in range(index + 1, end_index):
            #     next_timestamp, next_volume, next_open, next_high, next_low, next_close, next_chg, next_percent, next_turnoverrate, *_ = items[i]
            #     if (i == end_index - 1) and (next_close < close):
            #         next_utc_time = datetime.datetime.utcfromtimestamp(float(next_timestamp)/1000 + 86400).strftime("%Y-%m-%d %H:%M:%S.%f")
            #         print(f"has been drop! {stock_symbol}: {next_utc_time}")
            #         drop_count = drop_count + 1
            #         current_worst_possible_drop = (close - next_close) / close
            #         all_drop = all_drop + current_worst_possible_drop
            #         average_drop = all_drop / drop_count
            #         if current_worst_possible_drop > worst_possible_drop: 
            #             worst_possible_drop = current_worst_possible_drop
            #     if (next_high > close) and ((next_high - close) / close > 0.05):
            #         next_utc_time = datetime.datetime.utcfromtimestamp(float(next_timestamp)/1000 + 86400).strftime("%Y-%m-%d %H:%M:%S.%f")
            #         print(f"has been payback! {stock_symbol}: {next_utc_time}")
            #         right_count = right_count + 1
            #         break
                # if (next_low < close) and ((close - next_low) / close > 0.05):
                #     next_utc_time = datetime.datetime.utcfromtimestamp(float(next_timestamp)/1000 + 86400).strftime("%Y-%m-%d %H:%M:%S.%f")
                #     print(f"has been drop! {stock_symbol}: {next_utc_time}")
                #     drop_count = drop_count + 1
                #     break
        
        continue_drop_count = 0

    continue_drop_count = 0
    print(f"right stock: {right_stock}")


    # if right_count > 0:
    #     print(f"Current number of matches: {all_count}")
    #     print("Current Expectation rate: {:.2%}".format((right_count / all_count) * 0.045 - (1 - (right_count / all_count)) * average_drop))
    #     print("Current up satisfaction rate: {:.2%}".format(right_count / all_count))
    #     print("Current drop satisfaction rate: {:.2%}".format(drop_count / all_count))
    #     print("Average drop: {:.2%}".format(average_drop))
    #     print("Worst possible drop: {:.2%}".format(worst_possible_drop))
    #  and (next_turnoverrate > 1.0)
    #  and ((high - close) / (open_value - low) < 0.3)
