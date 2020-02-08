import ccxt

bitmex   = ccxt.bitmex()
exchange_id = 'bitmex'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'timeout': 30000,
    'enableRateLimit': True,
})

# hitbtc_markets = hitbtc.load_markets()

# print(hitbtc.id, hitbtc_markets)
# print(bitmex.id, bitmex.load_markets())
# print(huobipro.id, huobipro.load_markets())

# print(hitbtc.fetch_order_book(hitbtc.symbols[0]))
# print(bitmex.fetch_markets())
orderbook = bitmex.fetch_order_book('BTC/USD')

bids = orderbook['bids']
asks = orderbook['asks']

print("bids = " + str(bids))
print("asks = " + str(asks))

spread = []
for i in range(min(len(bids), len(asks))):
    spread.append(asks[i][0] - bids[i][0])

print("spread = " + str(spread))
# print(huobipro.fetch_trades('LTC/CNY'))

# print(exmo.fetch_balance())

# sell one ฿ for market price and receive $ right now
# print(exmo.id, exmo.create_market_sell_order('BTC/USD', 1))

# limit buy BTC/EUR, you pay €2500 and receive ฿1  when the order is closed
# print(exmo.id, exmo.create_limit_buy_order('BTC/EUR', 1, 2500.00))

# pass/redefine custom exchange-specific order params: type, amount, price, flags, etc...
# kraken.create_market_buy_order('BTC/USD', 1, {'trading_agreement': 'agree'})