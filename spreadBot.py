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
                
        # limit orders

        buy_limit_order = (self.bitmex.create_order(self.symbol, order_type, 'buy', int(quantity+0.5), (buy_price), params))
        print("buy limit placed")

        sell_limit_order = (self.bitmex.create_order(self.symbol, order_type, 'sell', int(quantity+0.5), (sell_price), params))
        print("sell limit placed")

        # stop loss orders
        order_type = 'Stop'
        params = {
        'stopPrice': buy_price  + 10,  # if needed
        }

        buy_stop_loss_order = self.bitmex.create_order(self.symbol, order_type, 'buy', int(quantity+0.5), None, params)
        print("buy stop loss placed")


        params = {
        'stopPrice': sell_price  - 10,  # if needed
        }

        sell_stop_loss_order = self.bitmex.create_order(self.symbol, order_type, 'sell', int(quantity+0.5), None, params)
        print("sell stop loss placed")
        

        while True:
            # if buy limit order is filled but sell limit order is still open
            if (self.bitmex.fetch_order(buy_limit_order['info']['orderID'])['status'] != 'open') and (self.bitmex.fetch_order(sell_limit_order['info']['orderID'])['status'] == 'open'):    
                
                # if sell stop loss order is filled
                if (self.bitmex.fetch_order(sell_stop_loss_order['info']['orderID'])['status'] != 'open'):

                    # cancel sell limit order
                    self.bitmex.cancel_order(sell_limit_order['info']['orderID'])
                    print("Canceled sell limit order")
                    print("Buy limit order filled and sell stop loss order filled")

                    break
                # if sell stop loss order is not filled
                else:
                    # cancel sell limit order 
                    self.bitmex.cancel_order(sell_limit_order['info']['orderID'])
                    print("Canceled sell limit order")                

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

            # if sell limit order is filled but buy limit order is still open
            elif (self.bitmex.fetch_order(buy_limit_order['info']['orderID'])['status'] == 'open') and (self.bitmex.fetch_order(sell_limit_order['info']['orderID'])['status'] != 'open'):    
                # if buy stop loss order is filled
                if (self.bitmex.fetch_order(buy_stop_loss_order['info']['orderID'])['status'] != 'open'):

                    # cancel buy limit order
                    self.bitmex.cancel_order(buy_limit_order['info']['orderID'])
                    print("Canceled buy limit order")                
                    print("Sell limit order filled and buy stop loss order filled")
                    break
                # if buy stop loss order is not filled
                else:
                    # cancel buy limit order 
                    self.bitmex.cancel_order(sell_limit_order['info']['orderID'])
                    print("Canceled buy limit order")                

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
            elif (self.bitmex.fetch_order(buy_limit_order['info']['orderID'])['status'] != 'open') and (self.bitmex.fetch_order(sell_limit_order['info']['orderID'])['status'] != 'open'):
                print("Both buy and sell limit order filled")
                break    
            elif (self.bitmex.fetch_order(buy_limit_order['info']['orderID'])['status'] == 'open') and (self.bitmex.fetch_order(sell_limit_order['info']['orderID'])['status'] == 'open'):
                print("Both buy and sell limit order not filled --> Waiting until one of them fills")
                
                if (self.bitmex.fetch_order(buy_stop_loss_order['info']['orderID'])['status'] != 'open'):
                    self.bitmex.cancel_order(buy_limit_order['info']['orderID'])
                    print("Buy stop loss order activated --> Canceled buy limit order" )
               
                elif (self.bitmex.fetch_order(sell_stop_loss_order['info']['orderID'])['status'] != 'open'):
                    self.bitmex.cancel_order(sell_limit_order['info']['orderID'])
                    print("Sell stop loss order activated --> Canceled sell limit order" )

                elif (self.bitmex.fetch_order(sell_stop_loss_order['info']['orderID'])['status'] != 'open') and (self.bitmex.fetch_order(buy_stop_loss_order['info']['orderID'])['status'] != 'open'):
                    self.bitmex.cancel_order(buy_limit_order['info']['orderID'])
                    self.bitmex.cancel_order(sell_limit_order['info']['orderID'])

                    print("Canceled both sell and buy limit order")
                    break
 

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

    apiKey = 'Gd5LBVd5KJKD2rv0RNQJ-Dek'
    secretKey = 'pzgmaHVKvxuym7BZA0LWnlR9WUdjAyzFHqFQawMht0hdCCV2'
    trade_amount = 1
    leverage = 100
    spread_bot = spreadBot(apiKey, secretKey, trade_amount, leverage)

    # spread_bot.plot_data('data.csv')
    spread_bot.run()

    # while True:
    #     try:
    #         spread_bot.run()
    #     except Exception as e: print(e)

