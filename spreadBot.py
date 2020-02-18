import ccxt
import time
import pandas as pd
import matplotlib.pyplot as plt
import csv

class spreadBot():

    def __init__(self, apiKey, secretKey, trade_amount, leverage, stop_price_difference):
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
        self.stop_price_difference = stop_price_difference

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

    def getBidAsk(self):
        orderbook = self.bitmex.fetch_order_book(self.symbol)
        bids = orderbook['bids']
        asks = orderbook['asks'] 

        buy_price = asks[0][0]
        sell_price = bids[0][0]
        buy_quantity = asks[0][1]
        sell_quantity = bids[0][1]        

        return buy_price, sell_price, buy_quantity, sell_quantity

    def executeBuyLimitOrder(self, quantity, price, leverage):
        order_type = 'limit'
        params = {'execInst': 'ParticipateDoNotInitiate',
        'leverage': leverage
        }        
        return self.bitmex.create_order(self.symbol, order_type, 'buy', int(quantity+0.5), price, params)

    def executeSellLimitOrder(self, quantity, price, leverage):
        order_type = 'limit'
        params = {'execInst': 'ParticipateDoNotInitiate',
        'leverage': leverage
        }        
        return self.bitmex.create_order(self.symbol, order_type, 'sell', int(quantity+0.5), price, params)

    def isFilled(self, order):
        if self.bitmex.fetch_order(order['info']['orderID'])['info']['ordStatus'] == 'Filled':
            return True

    def isCanceled(self, order):
        if self.bitmex.fetch_order(order['info']['orderID'])['info']['ordStatus'] == 'Canceled':
            return True

    def isOpen(self, order):
         if self.bitmex.fetch_order(order['info']['orderID'])['status'] == 'open':
            return True       

    def getOrderStatus(self, order):
        return self.bitmex.fetch_order(order['info']['orderID'])['info']['ordStatus']
    def getStatus(self, order):
        self.bitmex.fetch_order(order['info']['orderID'])['status']

    def timePassed(self, t0, t):
        return t - t0

    def cancelOrder(self, order):
        self.bitmex.cancel_order(order['info']['orderID'])


    def run(self):
        
        buy_limit_orders = []
        sell_limit_orders = []

        # quantity = min(buy_quantity, sell_quantity, btc_balance/2*buy_price, btc_balance/2*sell_price)
        quantity = self.trade_amount

        # limit orders
        buy_price, sell_price, buy_quantity, sell_quantity = self.getBidAsk()


        buy_limit_order = self.executeBuyLimitOrder(quantity, buy_price - 0.5, self.leverage)
        print("buy limit order placed: price = " + str(buy_price - 0.5))

        sell_limit_order = self.executeSellLimitOrder(self.trade_amount, sell_price + 0.5, self.leverage)
        print("sell limit order placed: price = " + str(sell_price + 0.5))
        
        sell_limit_orders.append(sell_limit_order)
        buy_limit_orders.append(buy_limit_order)

        t0 = time.time()
        timeThreshold = 10.0

        while True:
            if self.isFilled(buy_limit_orders[-1]) and not self.isFilled(sell_limit_orders[-1]):

                print("buy limit order filled, sell limit order not filled")
                print("t = " + str(self.timePassed(t0, time.time())))

                if self.timePassed(t0, time.time()) < timeThreshold:
                    print("time threshold not reached --> wait for sell limit order to fill")
                    continue
                else:
                    print("time threshold reached --> cancel sell limit order and place new one")
                    self.cancelOrder(sell_limit_orders[-1])
                    print("status of sell limit order is: " + str(self.getStatus(sell_limit_orders[-1])))

                    buy_price, sell_price, buy_quantity, sell_quantity = self.getBidAsk()
                    # sell_limit_order = self.executeSellLimitOrder(self.trade_amount, sell_price + 0.5, self.leverage)
                    sell_limit_orders.append(self.executeSellLimitOrder(self.trade_amount, sell_price + 0.5, self.leverage))

                    print("placed new sell limit order at price " + str(sell_price + 0.5) + ", with status: " + str(self.getStatus(sell_limit_orders[-1])))
                    t0 = time.time()

                    continue   
            elif self.isFilled(sell_limit_orders[-1]) and not self.isFilled(buy_limit_orders[-1]):

                print("sell limit order filled, buy limit order not filled")
                print("t = " + str(self.timePassed(t0, time.time())))

                if self.timePassed(t0, time.time()) < timeThreshold:
                    print("time threshold not reached --> wait for buy limit order to fill")
                    continue
                else:
                    print("time threshold reached --> cancel buy limit order and place new one")
                    self.cancelOrder(buy_limit_orders[-1])


                    print("status of buy limit order is: " + str(self.getStatus(buy_limit_orders[-1])))
                    buy_price, sell_price, buy_quantity, sell_quantity = self.getBidAsk()
                    # buy_limit_order = self.executeSellLimitOrder(self.trade_amount, buy_price - 0.5, self.leverage)
                    buy_limit_orders.append(self.executeSellLimitOrder(self.trade_amount, buy_price - 0.5, self.leverage))

                    print("placed new sell limit order at price " + str(buy_price - 0.5) + ", with status: " + str(self.getStatus(sell_limit_orders[-1])))
                    t0 = time.time()

                    continue   

            elif self.isFilled(sell_limit_orders[-1]) and self.isFilled(buy_limit_orders[-1]):
                print("both buy and sell limit order filled, buy price: " + str(buy_price - 0.5) + ", sell price: " + str(sell_price + 0.5))
                break

            elif not self.isFilled(sell_limit_orders[-1]) and not self.isFilled(buy_limit_orders[-1]):
                print("both buy and sell order not filled --> go back to begin of loop")


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

    # apiKey = 'Gd5LBVd5KJKD2rv0RNQJ-Dek'
    # secretKey = 'pzgmaHVKvxuym7BZA0LWnlR9WUdjAyzFHqFQawMht0hdCCV2'
    
    apiKey = '-GWrtORaoFmYRA_69-a1hbNv'
    secretKey = '0xFx3M8sixjKA9dGx1YyxHr9UPNBuZ7g-_CTK-_3feDSsUb7'

    trade_amount = 50
    leverage = 100
    # +- this difference depending on stop buy/sell order
    stop_price_difference = 15
    spread_bot = spreadBot(apiKey, secretKey, trade_amount, leverage, stop_price_difference)

    # spread_bot.plot_data('data.csv')
    spread_bot.run()

    # while True:
    #     try:
    #         spread_bot.run()
    #     except Exception as e: print(e)

