import ccxt
import time
    
class spreadBot():

    def __init__(self, apiKey, secretKey, trade_amount):
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

    def collect_data(self):
        f = open('data.csv', 'a')
        f.write("bid price, ask price, bid quantity, ask quantity, spread,\n")
        f.close()
        while True:
            try:
                orderbook = self.bitmex.fetch_order_book(self.symbol)
                bids = orderbook['bids']
                asks = orderbook['asks']

                with open('data.csv', 'a') as f:
                        f.write(str(bids[0][0]) + ", " + str(asks[0][0]) + ", " + str(bids[0][1]) + ", " + str(asks[0][1]) + ", " + str(asks[0][0] - bids[0][0]) + " USD,\n")
                time.sleep(2)
            except Exception as e: print(e) 


    def run(self):
        # btc_balance = self.bitmex.fetch_balance()['BTC']['free']

        orderbook = self.bitmex.fetch_order_book(self.symbol)
        bids = orderbook['bids']
        asks = orderbook['asks'] 

        sell_price = asks[0][0]
        buy_price = bids[0][0]
        # sell_quantity = asks[0][1]
        # buy_quantity = bids[0][1]

        spread = sell_price - buy_price

        # quantity = min(buy_quantity, sell_quantity, btc_balance/2*buy_price, btc_balance/2*sell_price)
        quantity = self.trade_amount

        order_type = 'limit'
        params = {'execInst': 'ParticipateDoNotInitiate'}


        if spread > 2: 
            self.bitmex.create_order(self.symbol, order_type, 'buy', int(quantity+0.5), (buy_price), params)
            self.bitmex.create_order(self.symbol, order_type, 'sell', int(quantity+0.5), (sell_price), params)
            print("trade executed")
        else:
            print("spread < 2")

if __name__ == "__main__":

    apiKey = 'UEQtbUhwe2UGg3l8csciE2nE'
    secretKey = '6cd2OBoFEr1_qzJmdlr2uoxAciRceJyGnQ5malr7aodnT4md'
    trade_amount = 0
    spread_bot = spreadBot(apiKey, secretKey, trade_amount)

    while True:
        try:
            spread_bot.run()
        except Exception as e: print(e)
