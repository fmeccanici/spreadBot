import ccxt
import time
import pandas as pd
import matplotlib.pyplot as plt
import csv

class spreadBot():

    def __init__(self, apiKey, secretKey, trade_amount, leverage):
        self.bitmex   = ccxt.bitmex(
            {
            'apiKey': apiKey,
            'secret': secretKey,
            'timeout': 30000,
            'enableRateLimit': True,
            }   
        )
        self.symbol = 'BTC/USD'
        self.balance = {'BTC':0.0, 'USD':0.0}
        self.trade_amount = trade_amount
        self.leverage = leverage

    def collect_data(self):
        f = open('data.csv', 'a')
        f.write("time, bid price, ask price, bid quantity, ask quantity, spread,\n")
        f.close()
        while True:
            try:
                orderbook = self.bitmex.fetch_order_book(self.symbol)
                bids = orderbook['bids']
                asks = orderbook['asks']

                with open('data.csv', 'a') as f:
                    f.write(time.ctime(time.time()) + ", " + str(bids[0][0]) + ", " + str(asks[0][0]) + ", " + str(bids[0][1]) + ", " + str(asks[0][1]) + ", " + str(asks[0][0] - bids[0][0]) + " USD,\n")
                time.sleep(2)
            except Exception as e: print(e) 


    def run(self):
        btc_balance = self.bitmex.fetch_balance()['BTC']['free']

        orderbook = self.bitmex.fetch_order_book(self.symbol)
        bids = orderbook['bids']
        asks = orderbook['asks'] 

        sell_price = asks[0][0]
        buy_price = bids[0][0]
        sell_quantity = asks[0][1]
        buy_quantity = bids[0][1]

        # spread = sell_price - buy_price

        quantity = min(buy_quantity, sell_quantity, btc_balance/2*buy_price, btc_balance/2*sell_price)
        # quantity = self.trade_amount

        order_type = 'limit'
        params = {'execInst': 'ParticipateDoNotInitiate',
        'leverage': self.leverage,
        }

        # if spread > 0: 
        buy_order = (self.bitmex.create_order(self.symbol, order_type, 'buy', int(quantity+0.5), (buy_price), params))
        # print(self.bitmex.fetch_order(buy_order['info']['orderID']))
        sell_order = (self.bitmex.create_order(self.symbol, order_type, 'sell', int(quantity+0.5), (sell_price), params))

        # print(buy_order)
        time.sleep(5)
        if buy_order['status'] == 'open' or sell_order['status'] == 'open':
            self.bitmex.cancel_order(buy_order['info']['orderID'])
            self.bitmex.cancel_order(sell_order['info']['orderID'])

        # print("trade executed")
        # else:
        #     print("spread < 2")


    def plot_data(self, data):
        aList=[]
        with open(data, 'r') as f:
            reader = csv.reader(f, skipinitialspace=False,delimiter=',', quoting=csv.QUOTE_NONE)
            for row in reader:
                aList.append(row)
        data = pd.DataFrame(aList)
        plt.plot(data[5][1:].map(lambda x: float(x.rstrip('USD '))))
        plt.ylabel('spread [USD]')
        plt.show()
        # data.plot(kind='line', x = data[0:], y = data[5:])

if __name__ == "__main__":

    apiKey = 'UVpDaNvrCQfx0qkIb4Dd0Uu4'
    secretKey = 'M-6-dwI2soY91fYsLgwPUQP9TDet0PifAnmDCMIhsAvQqNYt'
    trade_amount = 0
    leverage = 0
    spread_bot = spreadBot(apiKey, secretKey, trade_amount, leverage)

    # spread_bot.plot_data('data.csv')
    spread_bot.run()

    # while True:
        # try:
            # spread_bot.run()
            # spread_bot.collect_data()
        # except Exception as e: print(e)

