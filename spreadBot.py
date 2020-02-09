import ccxt
import time
    
class spreadBot():

    def __init__(self, apiKey, secretKey):
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

    def collect_data(self):
        f = open('data.csv', 'a')
        f.write("bid price, ask price, bid quantity, ask quantity, spread,\n")
        f.close()
        while True:
            try:
                # spread = []
                orderbook = self.bitmex.fetch_order_book(self.symbol)
                bids = orderbook['bids']
                asks = orderbook['asks']

                with open('data.csv', 'a') as f:
                        # spread.append(asks[i][0] - bids[i][0])
                        # print(asks[i][1])
                        f.write(str(bids[0][0]) + ", " + str(asks[0][0]) + ", " + str(bids[0][1]) + ", " + str(asks[0][1]) + ", " + str(asks[0][0] - bids[0][0]) + " USD,\n")
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

        spread = sell_price - buy_price

        # print(buy_price)
        # print(buy_quantity)
        quantity = min(buy_quantity, sell_quantity, btc_balance/2*buy_price, btc_balance/2*sell_price)
        order_type = 'limit'
        params = {'execInst': 'ParticipateDoNotInitiate'}

        # print(spread)
        # print(buy_price)

        if spread > 0: 
            self.bitmex.create_order(self.symbol, order_type, 'buy', int(quantity+0.5), (buy_price), params)
            self.bitmex.create_order(self.symbol, order_type, 'sell', int(quantity+0.5), (sell_price), params)
            print("trade exeuted")

if __name__ == "__main__":

    apiKey = 'UEQtbUhwe2UGg3l8csciE2nE'
    secretKey = '6cd2OBoFEr1_qzJmdlr2uoxAciRceJyGnQ5malr7aodnT4md'

    spread_bot = spreadBot(apiKey, secretKey)
    while True:
        try:
            spread_bot.run()
        except Exception as e: print(e)
# hitbtc_markets = hitbtc.load_markets()

# print(hitbtc.id, hitbtc_markets)
# print(bitmex.id, bitmex.load_markets())
# print(huobipro.id, huobipro.load_markets())

# print(hitbtc.fetch_order_book(hitbtc.symbols[0]))
# print(bitmex.fetch_markets())




# print("bids = " + str(bids))
# print("asks = " + str(asks))
   

# print("spread = " + str(spread))


# print(huobipro.fetch_trades('LTC/CNY'))

# print(exmo.fetch_balance())

# sell one ฿ for market price and receive $ right now
# print(exmo.id, exmo.create_market_sell_order('BTC/USD', 1))

# limit buy BTC/EUR, you pay €2500 and receive ฿1  when the order is closed
# print(exmo.id, exmo.create_limit_buy_order('BTC/EUR', 1, 2500.00))

# pass/redefine custom exchange-specific order params: type, amount, price, flags, etc...
# kraken.create_market_buy_order('BTC/USD', 1, {'trading_agreement': 'agree'})