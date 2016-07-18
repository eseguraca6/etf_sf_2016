from __future__ import print_function

import sys
import socket
import json
import time 

class Order():
    def __init__ (self, symbol, price, amount, direction, p, isConvert = False):
        self.symbol = symbol
        self.price = price
        self.amount = amount
        self.direction = direction
        self.isConvert = isConvert
        if symbol not in p.positions:
          p.positions[symbol] = 0

    def fill(self, fillAmount, p):
        

        self.amount -= fillAmount
        if self.isConvert: 
            if self.direction=="BUY":
                if self.symbol=="VALE":
                    p.position["VALE"]+=fillAmount
                    p.positions["VALBZ"]-=fillAmount
            else:
                if self.symbol=="VALE":
                    p.position["VALE"]-=fillAmount
                    p.positions["VALBZ"]+=fillAmount
        if self.direction == "BUY":
            p.positions[self.symbol] += fillAmount
        else:
            p.positions[self.symbol] -= fillAmount
        if self.symbol not in p.symbolsToAmountTraded:
          p.symbolsToAmountTraded[self.symbol] = 0
        p.symbolsToAmountTraded[self.symbol] += fillAmount

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
        self.highestBuyAmt={'GS':0, 'MS':0, 'WFC':0, 'XLF':0, 'VALBZ':0, 'VALE':0, 'BOND':0}
        self.cheapestSellAmt={'GS':0, 'MS':0, 'WFC':0, 'XLF':0, 'VALBZ':0, 'VALE':0, 'BOND':0}
        self.symbolToLimit = {'BOND':100, 'GS': 100, 'MS': 100, 'WFC': 100, 'XLF': 100, 'VALBZ': 10, 'VALE': 10}
        self.theEquities = {"WFC","MS","GS"}

        self.nextorderID = 0
        self.orders = {}
        self.exchange = exchange
        self.outstandingCancels = []
        self.symbolsToAmountTraded = {}

    #always return a positive number, clean up filled orders while at it
    def OutstandingOrders(self, symbol, direction):
        result = 0
        for orderID in self.orders:
            order = self.orders[orderID]
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
        for orderID in self.orders:
          if orderID in self.outstandingCancels : 
            continue
          order = self.orders[orderID]
          if order.symbol != symbol: 
            continue
          if order.direction == "BUY":
            order_price = order.price + halfSpread
          else:
            order_price = order.price - halfSpread
          if abs(fair_price - order_price) >= threshold:
            json_string = '{"type": "cancel", "order_id": %s}' % orderID
            self.waitUntilServerReady()
            print(json_string, file=sys.stderr) 
            print(json_string, file=self.exchange)
            self.outstandingCancels.append(orderID)

def connect(serv_addr, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((serv_addr, port))
    return (s, s.makefile('w+', 1))


def orderSec(symbol, direction, price, amount, p, exchange):
    orderID = p.nextorderID
    p.nextorderID += 1
    json_string = '{"type": "add", "order_id": '+ str(orderID) + ',"symbol": "' + symbol +'", "dir": "' +  direction + '", "price": ' + str(price) + ', "size" : ' + str(amount) + '}'
    print(json_string, file=sys.stderr)
    p.waitUntilServerReady()
    print(json_string, file=exchange)   
    p.orders[orderID] = Order(symbol, price, amount, direction, p)

def convert(symbol,direction,size,p):
    orderID=p.nextorderID
    p.nextorderID += 1
    json_string = '{"type": "convert", "order_id": '+ str(orderID) + ',"symbol": "' + symbol +'", "dir": "' +  direction + ', "size" : ' + str(amount) + '}'
    print(json_string, file=sys.stderr)
    p.waitUntilServerReady()
    print(json_string, file=exchange)   
    p.orders[orderID] = Order(symbol, 0, amount, direction, p ,True)


def tradeSymbol(symbol, exchange, fair_price, spread, p):
    bought = p.positions[symbol] + p.OutstandingOrders(symbol, "BUY")
    sold = -1 * p.positions[symbol] + p.OutstandingOrders(symbol, "SELL")
    limit = p.symbolToLimit[symbol] 

    buy_amount = limit - bought
    sell_amount = limit - sold
    
    if bought < limit and buy_amount > 0 :
        orderSec(symbol, "BUY", fair_price - spread, buy_amount, p, exchange)
    if sold < limit and sell_amount > 0:
        orderSec(symbol, "SELL", fair_price + spread, sell_amount, p, exchange)

def market_making(exchange):
    fair_price = 1000
    global p
    p.positions["BOND"] = 0
    #put in two orders for bonds
    orderSec("BOND", "BUY", fair_price -1 , 100, p, exchange)
    orderSec("BOND", "SELL", fair_price + 1, 100, p, exchange)
          

def parseData(msg, p):
    dat = json.loads(msg)
    if dat['type'] == "reject" and dat['error'] == "TRADING_CLOSED":
      sys.exit(2)
    elif dat['type'] == 'out':
        orderID = dat["order_id"]
        if orderID in p.outstandingCancels:
          p.outstandingCancels.remove(orderID)
          del p.orders[orderID]
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
        cheapestSellAmt=0
        highestBuyAmt=0
        for (val, size) in sell:
            if val < cheapSell:
              cheapSell = val
              cheapestSellAmt=size
        for (val, size) in buy:
            if val > highBuy:
              highBuy = val
              highestBuyAmt=size
        p.highestBuy[sym] = highBuy
        p.cheapestSellAmt[sym]=cheapestSellAmt
        p.highestBuyAmt[sym]=highestBuyAmt
        p.cheapestSell[sym] = cheapSell

    elif dat['type'] == "hello":
        syms = dat['symbols']
        for info in syms:
          theSym = info['symbol']
          position = info['position']
          p.positions[theSym] = position

def main():
    alpha=1
    s, exchange = connect("production",25000)

    json_string = '{"type": "hello", "team":"CUPCAKELY"}'
    print(json_string, file=exchange)
    hello_from_exchange = exchange.readline().strip()
    print("The exchange replied: %s" % str(hello_from_exchange),file = sys.stderr)
    
    global p
    p = Portfolio(exchange)
    parseData(hello_from_exchange, p)

    print("entering main loop", file = sys.stderr)

    
    price_VALE=0
    while True:
      market_making(exchange)

      if  p.highestBuy["VALBZ"] != 0 and p.cheapestSell["VALBZ"] !=0:
            #use EMA as the fair price
            if price_VALE==0: 
              price_VALE=int(round((p.highestBuy["VALBZ"] + p.cheapestSell["VALBZ"])/2.0))
            else:
              price_VALE=alpha*int(round((p.highestBuy["VALBZ"] + p.cheapestSell["VALBZ"])/2.0))+(1-alpha)*price_VALE
            p.CancelObsoleteOrders("VALE", price_VALE, p.halfSpread["VALE"])
            tradeSymbol("VALE", exchange, price_VALE, p.halfSpread["VALE"], p)

            if p.cheapestSell["VALBZ"]+10<p.highestBuy["VALE"]:
                amountToTrade=min(p.cheapestSellAmt["VALBZ"],p.highestBuyAmt["VALE"]) 
                orderSec("VALBZ","BUY",p.cheapestSell["VALBZ"], amountToTrade , p,exchange)
                convert("VALE","BUY",amountToTrade,p)
                orderSec("VALE","SELL",p.highestBuy["VALE"], amountToTrade , p,exchange)
            elif p.cheapestSell["VALE"]+10<p.highestBuy["VALBZ"]:
                amountToTrade=min(p.cheapestSellAmt["VALE"],p.highestBuyAmt["VALBZ"]) 
                orderSec("VALE","BUY",p.cheapestSell["VALE"], amountToTrade , p,exchange)
                convert("VALE","SELL",amountToTrade,p)
                orderSec("VALBZ","SELL",p.highestBuy["VALBZ"], amountToTrade , p,exchange)


      message = exchange.readline().strip()
      parseData(message, p)
      if message is not None:
        #chuck away book messages for now
        m_type = json.loads(message)['type']
        if m_type == 'book' or m_type == 'trade' or m_type == 'ack':
          pass
        else:  
          print("> %s" % str (message), file =sys.stderr)
      # have we got a message ? 

if __name__ == "__main__":
    main()
