from __future__ import print_function

import sys
import socket
import json
import time



def main():
    exchange = connect("production",25000)
    json_string = '{"type": "hello", "team":"CUPCAKELY"}'
    print(json_string, file=exchange)
    hello_from_exchange = exchange.readline().strip()
    print("The exchange replied:", hello_from_exchange, file=sys.stderr)
    p=Portfolio()
    while True:
    	bond_trading(p)
    	e_json= json.loads(exchange.readline().strip())
    	parseData(e_json,p)
    	time.sleep(0.01)

def parseData(e_json,p):
	dat = json.loads(e_json)
	if dat['type'] == "reject" and dat['error'] == "TRADING_CLOSED":
      sys.exit(2)
    elif dat['type'] == 'out':
        orderId = dat["order_id"]
        if orderId in p.outstandingCancels:
          p.outstandingCancels.remove(orderId)
          del p.orders[orderId]
    elif dat['type'] == "fill":
        order = p.orders[dat['order_id']]
        order.fill(dat['size'], p)
    elif dat['type'] == "trade" and dat['symbol'] not in ["BOND", "VALE"]:
        price = dat['price']
        size = dat['size']
        #updateFairPrice(dat['symbol'], price, size, p)
    elif dat['type'] == "book":
        sym = dat['symbol']
        sell = dat['sell']
        buy = dat['buy']
        cheapSell = 10000000
        highBuy = 0
        for (val, size) in sell:
            if val < cheapSell:
              cheapSell = val
        for (val, size) in buy:
            if val > highBuy:
              highBuy = val
        p.highestBuy[sym] = highBuy
        p.cheapestSell[sym] = cheapSell

def bond_trading(p):
	buyOrder=Order("add","BOND","BUY",99,100)
	buyOrder.make(p)
	sellOrder=Order("add","BOND","SELL",101,100)
	sellOrder.make(p)

class Order():
	orderID=0
	def __init__ (self,orderType,symbol,direction,price,size):
		self.type=orderType
		self.symbol=symbol
		self.dir=direction
		self.price=price
		self.size=size
		self.order_id=Order.orderID

	def make(self):
		if Portfolio.position["BOND"]>100 or Portfolio.position["BOND"]<-100: return
		newOrder=json.dumps(self.__dict__)
		print(newOrder,file=sys.stderr)
		print(newOrder,file=exchange)
		Order.orderID+=1

class Portfolio():
    def __init__(self, exchange):
        #symbol to Position
        self.xlfguess = 0
        self.lastOrderTime = time.time()
        #to update
        self.positions = {"GS": 0, "MS": 0, "WFC": 0, "XLF": 0, "VALE": 0, "VALBZ": 0}
        self.halfSpread = {"GS": 1, "MS": 1, "WFC": 1, "XLF": 6, "VALBZ": 5, "BOND": 1, "VALE": 5}
        self.highestBuy = {'GS':0, 'MS':0, 'WFC':0, 'XLF':0, 'VALBZ':0, 'VALE':0, 'BOND':0}
        self.cheapestSell = {'GS':0, 'MS':0, 'WFC':0, 'XLF':0, 'VALBZ':0, 'VALE':0, 'BOND':0}
        self.symbolToLimit = {'BOND':100, 'GS': 100, 'MS': 100, 'WFC': 100, 'XLF': 100, 'VALBZ': 10, 'VALE': 10}
        self.theEquities = {"WFC","MS","GS"}

        self.nextOrderId = 0
        self.orders = {}
        self.exchange = exchange
        self.outstandingCancels = []
        self.symbolsToAmountTraded = {}

    #always return a positive number, clean up filled orders while at it
    def OutstandingOrders(self, symbol, direction):
        result = 0
        for orderId in self.orders:
            order = self.orders[orderId]
            if order.symbol == symbol and order.direction == direction:
              result += order.amount

        return result

    def waitUntilServerReady(self):
        while time.time() - self.lastOrderTime < 0.01:
          continue
        self.lastOrderTime = time.time()
        return
    
    def CancelObsoleteOrders(self, symbol, fair_price, halfSpread):
        threshold=2
        for orderId in self.orders:
          if orderId in self.outstandingCancels : 
            continue
          order = self.orders[orderId]
          if order.symbol != symbol: 
            continue
          if order.direction == "BUY":
            order_price = order.price + halfSpread
          else:
            order_price = order.price - halfSpread
          if abs(fair_price - order_price) >= threshold:
            json_string = '{"type": "cancel", "order_id": %s}' % orderId
            self.waitUntilServerReady()
            print(json_string, file=sys.stderr) 
            print(json_string, file=self.exchange)
            self.outstandingCancels.append(orderId)




if __name__ == "__main__":
    main()