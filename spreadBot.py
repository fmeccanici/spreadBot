import ccxt
import time
    

f = open('data.csv', 'a')
f.write("bid price, ask price, bid quanitity, ask quantity, spread,\n")
f.close()


bitmex   = ccxt.bitmex()
exchange_id = 'bitmex'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'apiKey': 'UEQtbUhwe2UGg3l8csciE2nE',
    'secret': '6cd2OBoFEr1_qzJmdlr2uoxAciRceJyGnQ5malr7aodnT4md',
    'timeout': 30000,
    'enableRateLimit': True,
})

# hitbtc_markets = hitbtc.load_markets()

# print(hitbtc.id, hitbtc_markets)
# print(bitmex.id, bitmex.load_markets())
# print(huobipro.id, huobipro.load_markets())

# print(hitbtc.fetch_order_book(hitbtc.symbols[0]))
# print(bitmex.fetch_markets())




# print("bids = " + str(bids))
# print("asks = " + str(asks))
   

# print("spread = " + str(spread))

while True:
    # spread = []
    orderbook = bitmex.fetch_order_book('BTC/USD')
    bids = orderbook['bids']
    asks = orderbook['asks']

    with open('data.csv', 'a') as f:
        for i in range(min(len(bids), len(asks))):
            # spread.append(asks[i][0] - bids[i][0])
            # print(asks[i][1])
            f.write(str(bids[i][0]) + ", " + str(asks[i][0]) + ", " + str(bids[i][1]) + ", " + str(asks[i][1]) + ", " + str(asks[i][0] - bids[i][0]) + " USD,\n")
    time.sleep(1)

# print(huobipro.fetch_trades('LTC/CNY'))

# print(exmo.fetch_balance())

# sell one ฿ for market price and receive $ right now
# print(exmo.id, exmo.create_market_sell_order('BTC/USD', 1))

# limit buy BTC/EUR, you pay €2500 and receive ฿1  when the order is closed
# print(exmo.id, exmo.create_limit_buy_order('BTC/EUR', 1, 2500.00))

# pass/redefine custom exchange-specific order params: type, amount, price, flags, etc...
# kraken.create_market_buy_order('BTC/USD', 1, {'trading_agreement': 'agree'})