import ccxt
import time
import pandas as pd
import matplotlib.pyplot as plt
import csv
import numpy as np

class spreadBot():

    def __init__(self, apiKey, secretKey, trade_amount, leverage, stop):
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
        self.stop = stop

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

    def executeBuyMarketStopLossOrder(self, quantity, price, leverage, stop):
        order_type = 'Stop'
        params = {
            'stopPx': price + stop
        }
        return self.bitmex.create_order(self.symbol, order_type, 'buy', int(quantity+0.5), None, params)

    def executeSellMarketStopLossOrder(self, quantity, price, leverage, stop):
        order_type = 'Stop'
        params = {
            'stopPx': price - stop
        }
        return self.bitmex.create_order(self.symbol, order_type, 'sell', int(quantity+0.5), None, params)


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


    def getOrderbook(self, depth):
        return self.bitmex.fetch_order_book(self.symbol, depth)

    def getFirstPrices(self):
        orderbook = self.getOrderBook(1)
        bids = orderbook['bids']
        asks = orderbook['asks'] 

        buy_price = asks[0][0]
        sell_price = bids[0][0]

        return buy_price, sell_price
        
    def getSpread(self):
        buy_price, sell_price = self.getFirstPrices()

        return sell_price - buy_price    

    def getMarketDirection(self, previous_price, current_price):
        orderbook = self.getOrderbook()

    def isListEmpty(self, list):
        return len(list) == 0

    def runLimitStopPlacementBot(self):
        buy_limit_orders = []
        sell_limit_orders = []
        buy_stop_orders = []
        sell_stop_orders = []

        # quantity = min(buy_quantity, sell_quantity, btc_balance/2*buy_price, btc_balance/2*sell_price)
        quantity = self.trade_amount

        orderbook = self.getOrderbook(3)
        bids = orderbook['bids']
        asks = orderbook['asks'] 

        # get first prices in orderbook
        buy_price = bids[0][0]
        sell_price = asks[0][0]

        buy_limit_order = self.executeBuyLimitOrder(quantity, buy_price, self.leverage)
        print("buy limit order placed: price = " + str(buy_price))

        sell_limit_order = self.executeSellLimitOrder(self.trade_amount, sell_price, self.leverage)
        print("sell limit order placed: price = " + str(sell_price))
        
        sell_limit_orders.append(sell_limit_order)
        buy_limit_orders.append(buy_limit_order)


        while True:
            if self.isFilled(buy_limit_orders[-1]) and not self.isFilled(sell_limit_orders[-1]):
                print('buy limit order filled, sell limit order not filled')

                if self.isListEmpty(sell_stop_orders):
                    sell_stop_orders.append(self.executeSellMarketStopLossOrder(quantity, sell_price, self.leverage, self.stop))
                    print('posted sell market stop loss order')
                else:
                    if self.isFilled(sell_stop_orders[-1]):
                        self.cancelOrder(sell_limit_orders[-1])
                        print('sell stop loss order filled --> sell limit order canceled')
                        break
                    elif self.isFilled(sell_limit_orders[-1]):
                        self.cancelOrder(sell_stop_orders[-1])
                        print('sell limit order filled --> sell stop loss canceled')
                        break
                    else:
                        print('sell market stop loss order or limit order not filled yet')
                        continue
 
            elif self.isFilled(sell_limit_orders[-1]) and not self.isFilled(buy_limit_orders[-1]):
                print('sell limit order filled, buy limit order not filled')

                if self.isListEmpty(buy_stop_orders):
                    buy_stop_orders.append(self.executeBuyMarketStopLossOrder(quantity, buy_price, self.leverage, self.stop))
                    print('posted buy market stop loss order')

                else:
                    if self.isFilled(buy_stop_orders[-1]):
                        self.cancelOrder(buy_limit_orders[-1])
                        print('buy stop loss order filled --> buy stop loss canceled')

                        break
                    elif self.isFilled(buy_limit_orders[-1]):
                        self.cancelOrder(buy_stop_orders[-1])
                        print('buy limit order filled --> buy stop loss canceled')

                        break
                    else:
                        print('buy market stop loss order or limit order not filled yet')

                        continue


            elif self.isFilled(sell_limit_orders[-1]) and self.isFilled(buy_limit_orders[-1]):
                print("both buy and sell limit order filled, buy price: " + str(buy_price) + ", sell price: " + str(sell_price))

                if not self.isListEmpty(sell_stop_orders):
                    if not self.isFilled(sell_stop_orders[-1]):
                        self.cancelOrder(sell_stop_orders[-1])
                        print('sell stop loss order not filled --> canceled')
                elif not self.isListEmpty(buy_stop_orders):
                    if not self.isFilled(buy_stop_orders[-1]):
                        self.cancelOrder(buy_stop_orders[-1])
                        print('buy stop loss order not filled --> canceled')
                break

            elif not self.isFilled(sell_limit_orders[-1]) and not self.isFilled(buy_limit_orders[-1]):
                print("both buy and sell order not filled --> cancel both")
                self.cancelOrder(buy_limit_orders[-1])
                print("buy limit order canceled")
                self.cancelOrder(sell_limit_orders[-1])
                print("sell limit order canceled")

                break

    def runSpreadBot(self):
            buy_limit_orders = []
            sell_limit_orders = []
            
            buy_prices = np.zeros(2)
            sell_prices = np.zeros(2)

            with open("log_file.txt", 'a') as log_file:
                while True:
                    try:
                        orderbook = self.getOrderbook(1)
                        bids = orderbook['bids']
                        asks = orderbook['asks'] 

                        buy_prices[0] = buy_prices[1]
                        sell_prices[0] = sell_prices[1]

                        buy_prices[1] = asks[0][0]
                        sell_prices[1] = bids[0][0]

                        spread = buy_prices[1] - sell_prices[1]  

                        quantity = self.trade_amount

                        if spread > 0.5 and buy_prices[0] != 0.0:

                            # market goes up
                            if buy_prices[0] - buy_prices[1] < 0:
                                buy_price = buy_prices[1] + 1.0
                                sell_price = sell_prices[1] + 1.5
                                try:
                                    buy_limit_order = self.executeBuyLimitOrder(quantity, buy_price, self.leverage)
                                    sell_limit_order = self.executeSellLimitOrder(quantity, sell_price, self.leverage)
                                    with open("executed_trades.txt", 'a') as f:
                                        f.write(str(buy_limit_order) + '\n \n')
                                        f.write(str(sell_limit_order) + '\n \n')
                                except:
                                    continue

                            # market goes down
                            elif buy_prices[1] - buy_prices[0] < 0:
                                buy_price = buy_prices[1] - 1.5
                                sell_price = sell_prices[1] - 1
                                try:
                                    buy_limit_order = self.executeBuyLimitOrder(quantity, buy_price, self.leverage)
                                    sell_limit_order = self.executeSellLimitOrder(quantity, sell_price, self.leverage)
                                    with open("executed_trades.txt", 'a') as f:
                                        f.write(str(buy_limit_order) + '\n \n')
                                        f.write(str(sell_limit_order) + '\n \n')
                                except:
                                    continue
                        else:
                            print("Spread = " + str(spread))
                    except Exception as e:
                        print(e)
                        log_file.write(str(e) + "\n")
                        continue

    def runLimitOrderPlacementLoop(self, buy_limit_order, sell_limit_order, buy_price, sell_price):
        t0 = time.time()
        timeThreshold = 10.0

        while True:
            if self.isFilled(buy_limit_orders[-1]) and not self.isFilled(sell_limit_orders[-1]):

                print("buy limit order filled, sell limit order not filled")
                print("t = " + str(round(self.timePassed(t0, time.time()))))

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

    def runLimitOrderPlacement(self):
        
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

    apiKey = 'xAdGLZ3ahuZSv2lwwgO9zK6Q'
    secretKey = 'OIxtUgSWI-Oq2Eoig6k0GG3T1bN8_Gl6mp84c-TPU0W1T9qO'
    
    # apiKey = '-GWrtORaoFmYRA_69-a1hbNv'
    # secretKey = '0xFx3M8sixjKA9dGx1YyxHr9UPNBuZ7g-_CTK-_3feDSsUb7'

    trade_amount = 50
    leverage = 100
    stop = 100

    spread_bot = spreadBot(apiKey, secretKey, trade_amount, leverage, stop)

    while True:
        spread_bot.runLimitStopPlacementBot()

