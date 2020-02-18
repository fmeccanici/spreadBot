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


    def run(self):
        btc_balance = self.bitmex.fetch_balance()['BTC']['free']

        orderbook = self.bitmex.fetch_order_book(self.symbol)
        bids = orderbook['bids']
        asks = orderbook['asks'] 

        buy_price = asks[0][0]-0.5
        sell_price = bids[0][0]+0.5
        buy_quantity = asks[0][1]
        sell_quantity = bids[0][1]

        # print("best buy price: " + str(buy_price))
        # print("best sell price: " + str(sell_price))
        # spread = sell_price - buy_price
        
        # quantity = min(buy_quantity, sell_quantity, btc_balance/2*buy_price, btc_balance/2*sell_price)
        quantity = self.trade_amount

        order_type = 'limit'
        params = {'execInst': 'ParticipateDoNotInitiate',
        'leverage': self.leverage,
        }
                
        # print(self.bitmex.fetch_order("6ca6b8db-07c4-ecdf-e559-bd1367ebd6e6")['info']['ordStatus'])

        
        # limit orders
        buy_limit_order = (self.bitmex.create_order(self.symbol, order_type, 'buy', int(quantity+0.5), (buy_price), params))
        print("buy limit order placed: price = " + str(buy_price))

        sell_limit_order = (self.bitmex.create_order(self.symbol, order_type, 'sell', int(quantity+0.5), (sell_price), params))
        print("sell limit placed: price = " + str(sell_price))
        

        # stop loss orders
        order_type = 'Stop'
        params = {
        'stopPx': buy_price  + self.stop_price_difference,  # if needed
        }

        buy_stop_loss_order = self.bitmex.create_order(self.symbol, order_type, 'buy', int(quantity+0.5), None, params)
        print("buy stop loss placed: price = " + str(params['stopPx']))

        params = {
        'stopPx': sell_price  - self.stop_price_difference,  # if needed
        }

        sell_stop_loss_order = self.bitmex.create_order(self.symbol, order_type, 'sell', int(quantity+0.5), None, params)
        print("sell stop loss placed: price = " + str(params['stopPx']))
        

        t_cancel = 30
        t = 0.0
        t0 = time.time()
        while True:
            print("Starting loop...")
            print("t = " + str(t))
            print("sell limit order status: " + self.bitmex.fetch_order(sell_limit_order['info']['orderID'])['info']['ordStatus'])
            print("buy limit order status: " + self.bitmex.fetch_order(buy_limit_order['info']['orderID'])['info']['ordStatus'])
            print("sell stop loss order status: " + self.bitmex.fetch_order(sell_stop_loss_order['info']['orderID'])['info']['ordStatus'])
            print("buy stop loss order status: " + self.bitmex.fetch_order(buy_stop_loss_order['info']['orderID'])['info']['ordStatus'])

            # if buy limit order is filled but sell limit order is still open
            if (self.bitmex.fetch_order(buy_limit_order['info']['orderID'])['info']['ordStatus'] == 'Filled') and (self.bitmex.fetch_order(sell_limit_order['info']['orderID'])['status'] == 'open'):    
                if self.bitmex.fetch_order(buy_stop_loss_order['info']['orderID'])['status'] == 'open':
                    self.bitmex.cancel_order(buy_stop_loss_order['info']['orderID'])
                    print("Buy limit order filled --> Canceled buy stop loss order")

                # if sell stop loss order is filled
                if (self.bitmex.fetch_order(sell_stop_loss_order['info']['orderID'])['info']['ordStatus'] == 'Filled'):

                    # cancel sell limit order
                    self.bitmex.cancel_order(sell_limit_order['info']['orderID'])
                    print("Canceled sell limit order")
                    print("Buy limit order filled and sell stop loss order filled")

                    break
                # if sell stop loss order is not filled
                elif self.bitmex.fetch_order(sell_stop_loss_order['info']['orderID'])['status'] == 'open':
                    
                    if (self.bitmex.fetch_order(sell_limit_order['info']['orderID'])['info']['ordStatus'] == 'Filled') and (t <= t_cancel):
                        print("Sell limit order filled within " + str(t) + " s")
                        break
                    elif (self.bitmex.fetch_order(sell_limit_order['info']['orderID'])['status'] == 'open') and (t > t_cancel):

                        # t = time.time() - t0

                        # cancel sell limit order 
                        self.bitmex.cancel_order(sell_limit_order['info']['orderID'])
                        print("Canceled sell limit order: t = " + str(t) + "s")                

                        # get orderbook to place new sell limit order
                        orderbook = self.bitmex.fetch_order_book(self.symbol)
                        bids = orderbook['bids']

                        sell_price = bids[0][0]+0.5
                        sell_quantity = bids[0][1]

                        # quantity = min(buy_quantity, sell_quantity, btc_balance/2*buy_price, btc_balance/2*sell_price)
                        quantity = self.trade_amount

                        order_type = 'limit'
                        params = {'execInst': 'ParticipateDoNotInitiate',
                        'leverage': self.leverage,
                        }
                        
                        # place new sell limit order
                        sell_limit_order = (self.bitmex.create_order(self.symbol, order_type, 'sell', int(quantity+0.5), (sell_price), params)) 
                        print("Placed new sell limit order")
                        t = 0.0
                        print("Set t = 0.0s")

                    elif (self.bitmex.fetch_order(sell_limit_order['info']['orderID'])['status'] == 'open') and (t < t_cancel):
                        print("Waiting for sell limit order to fill")
                        t = time.time() - t0
                        continue


            # if sell limit order is filled but buy limit order is still open
            elif (self.bitmex.fetch_order(buy_limit_order['info']['orderID'])['status'] == 'open') and (self.bitmex.fetch_order(sell_limit_order['info']['orderID'])['info']['ordStatus'] == 'Filled'):    
                if self.bitmex.fetch_order(sell_stop_loss_order['info']['orderID'])['status'] == 'open':
                    self.bitmex.cancel_order(sell_stop_loss_order['info']['orderID'])
                    print("Sell limit order filled --> Canceled sell stop loss order")

                # if buy stop loss order is filled
                if (self.bitmex.fetch_order(buy_stop_loss_order['info']['orderID'])['info']['ordStatus'] == 'Filled'):
                    # cancel buy limit order
                    self.bitmex.cancel_order(buy_limit_order['info']['orderID'])
                    print("Canceled buy limit order")                
                    print("Sell limit order filled and buy stop loss order filled")
                    break
                # if buy stop loss order is not filled
                elif self.bitmex.fetch_order(buy_stop_loss_order['info']['orderID'])['status'] == 'open':

                    if (self.bitmex.fetch_order(buy_limit_order['info']['orderID'])['info']['ordStatus'] == 'Filled') and (t <= t_cancel):
                        print("Buy limit order filled within "  + str(t) + " s")
                        break
                    elif (self.bitmex.fetch_order(buy_limit_order['info']['orderID'])['status'] == 'open') and (t > t_cancel):
                        # t = time.time() - t0

                        # cancel buy limit order 
                        self.bitmex.cancel_order(sell_limit_order['info']['orderID'])
                        print("Canceled buy limit order: t = " + str(t) + " s")                

                        # get orderbook to place new sell limit order
                        orderbook = self.bitmex.fetch_order_book(self.symbol)
                        asks = orderbook['asks'] 

                        buy_price = asks[0][0]-0.5
                        buy_quantity = asks[0][1]

                        # quantity = min(buy_quantity, sell_quantity, btc_balance/2*buy_price, btc_balance/2*sell_price)
                        quantity = self.trade_amount

                        order_type = 'limit'
                        params = {'execInst': 'ParticipateDoNotInitiate',
                        'leverage': self.leverage,
                        }
                        

                        # place new buy limit order
                        buy_limit_order = (self.bitmex.create_order(self.symbol, order_type, 'buy', int(quantity+0.5), (buy_price), params))
                        print("Placed new buy limit order")
                        t = 0.0
                        print("Set t = 0.0s")
                        continue

                    elif (self.bitmex.fetch_order(buy_limit_order['info']['orderID'])['status'] == 'open') and (t < t_cancel):
                        print("Waiting for buy limit order to fill")
                        t = time.time() - t0
                        continue



            elif (self.bitmex.fetch_order(buy_limit_order['info']['orderID'])['info']['ordStatus'] == 'Filled') and (self.bitmex.fetch_order(sell_limit_order['info']['orderID'])['info']['ordStatus'] == 'Filled'):
                print("Both buy and sell limit order filled")
                if (self.bitmex.fetch_order(sell_stop_loss_order['info']['orderID'])['status']) == 'open':
                    self.bitmex.cancel_order(sell_stop_loss_order['info']['orderID'])
                    print("Canceled sell stop loss order")
                if (self.bitmex.fetch_order(buy_stop_loss_order['info']['orderID'])['status']) == 'open':
                    self.bitmex.cancel_order(buy_stop_loss_order['info']['orderID'])
                    print("Canceled buy stop loss order")
                
                break    
            elif (self.bitmex.fetch_order(buy_limit_order['info']['orderID'])['status'] == 'open') and (self.bitmex.fetch_order(sell_limit_order['info']['orderID'])['status'] == 'open'):
                print("Both buy and sell limit order not filled --> Waiting until one of them fills")
                
                if (self.bitmex.fetch_order(buy_stop_loss_order['info']['orderID'])['info']['ordStatus'] == 'Filled'):
                    self.bitmex.cancel_order(buy_limit_order['info']['orderID'])
                    print("Buy stop loss order activated --> Canceled buy limit order" )
               
                elif (self.bitmex.fetch_order(sell_stop_loss_order['info']['orderID'])['info']['ordStatus'] == 'Filled'):
                    self.bitmex.cancel_order(sell_limit_order['info']['orderID'])
                    print("Sell stop loss order activated --> Canceled sell limit order" )

                elif (self.bitmex.fetch_order(sell_stop_loss_order['info']['orderID'])['info']['ordStatus'] == 'Filled') and (self.bitmex.fetch_order(buy_stop_loss_order['info']['orderID'])['info']['ordStatus'] == 'Filled'):
                    self.bitmex.cancel_order(buy_limit_order['info']['orderID'])
                    self.bitmex.cancel_order(sell_limit_order['info']['orderID'])

                    print("Canceled both sell and buy limit order")
                    break
                continue


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

