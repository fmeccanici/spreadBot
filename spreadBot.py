import bitmex
import requests, json
import ccxt

class spreadBot():
    def __init__(self):
        # self.client = bitmex.bitmex(test=False)
        self.orderbook = []
        self.bitmex = ccxt.bitmex()
        self.exchange_class = getattr(ccxt, exchange_id)
        self.exchange = self.exchange_class({
            'apiKey': 'YOUR_API_KEY',
            'secret': 'YOUR_SECRET',
            'timeout': 30000,
            'enableRateLimit': True,
        })
    def _set_orderbook(self, pair, depth):
        # response = "https://www.bitmex.com/api/v1/trade?filter=%7B%22side%22%3A%22Buy%22%7D&count=100"
        # response = requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=" + pair + "&depth=" + str(depth) + "/filter").json()
        # result = self.client.Quote.Quote_get(symbol="XBTUSD", reverse=True, count=1).result()
        # response = requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=" + pair + "&depth=" + str(depth)).json()
        # response = self.client.Trade.Trade_get(symbol="XBTUSD", count=1, reverse=True).result() 
        
        self.orderbook = self.bitmex.fetch_order_book('BTC/USD')    
        # return result

    

    def _get_buy_sell_orders(self ):
        
        # iSellOrders = range(0,len(orderbook)/2)
        # iBuyOrders = range(len(orderbook/2,len(orderbook-1)))

        SellOrders = []
        BuyOrders = []
        
        for order in self.orderbook:
            if order['side'] == 'Sell':
                SellOrders.append(order)
            elif order['side'] == 'Buy':
                BuyOrders.append(order)

        return SellOrders, BuyOrders

    def _get_prices_quantity(self):
        SellPrices = []
        BuyPrices = []
        SellQuantity = []
        BuyQuantity = []

        for order in self.orderbook:
            if order['side'] == 'Sell':
                SellPrices.append(order['price'])
                SellQuantity.append(order['size'])
            elif order['side'] == 'Buy':
                BuyPrices.append(order['price'])
                BuyQuantity.append(order['size'])
        return SellPrices, SellQuantity, BuyPrices, BuyQuantity

    def print_buy_sell_orders(self):
        SellPrices, SellQuantity, BuyPrices, BuyQuantity = self._get_prices_quantity()
        print(SellPrices)
        print(BuyPrices)

    def get_spread(self, pair, depth):
        self._set_orderbook(pair, depth)
        self._get_prices_quantity()

        SellPrices, SellQuantity, BuyPrices, BuyQuantity = self._get_prices_quantity()
        spread = []
        for i in range(min(len(BuyPrices), len(SellPrices))):
            spread.append(float(SellPrices[i]) - float(BuyPrices[i]))
        return spread


if __name__ == "__main__":
    spread_bot = spreadBot()
    pair = 'XBTUSD'
    orderbook_depth = 10
    # print(spread_bot.get_orderbook(pair, orderbook_depth))
    spread_bot._set_orderbook(pair, orderbook_depth)
    print(spread_bot._get_buy_sell_orders())
    spread_bot.print_buy_sell_orders()
    print("spread = " + str(spread_bot.get_spread(pair, orderbook_depth)))
