 # fork from etc0 by team wessel
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
        if self.isConvert: return
        self.amount -= fillAmount
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
        self.symbolToLimit = {'BOND':100, 'GS': 100, 'MS': 100, 'WFC': 100, 'XLF': 100, 'VALBZ': 10, 'VALE': 10}
        self.theEquities = {"WFC","MS","GS"}
        self.highestBuyAmt={'GS':0, 'MS':0, 'WFC':0, 'XLF':0, 'VALBZ':0, 'VALE':0, 'BOND':0}
        self.cheapestSellAmt={'GS':0, 'MS':0, 'WFC':0, 'XLF':0, 'VALBZ':0, 'VALE':0, 'BOND':0}
        self.buyList={'GS':[], 'MS':[], 'WFC':[], 'XLF':[], 'VALBZ':[], 'VALE':[], 'BOND':[]}
        self.sellList={'GS':[], 'MS':[], 'WFC':[], 'XLF':[], 'VALBZ':[], 'VALE':[], 'BOND':[]}
        self.balist=set()
        self.currentBuy={'GS':0, 'MS':0, 'WFC':0, 'XLF':0, 'VALBZ':0, 'VALE':0, 'BOND':0}
        self.currentSell={'GS':10000000, 'MS':10000000, 'WFC':10000000, 'XLF':10000000, 'VALBZ':10000000, 'VALE':10000000, 'BOND':10000000}
        self.currentBuyID={'GS':-1, 'MS':-1, 'WFC':-1, 'XLF':-1, 'VALBZ':-1, 'VALE':-1, 'BOND':-1}
        self.currentSellID={'GS':-1, 'MS':-1, 'WFC':-1, 'XLF':-1, 'VALBZ':-1, 'VALE':-1, 'BOND':-1}
        self.nextOrderID = 0
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
        print("try cancel orders out of" +str(fair_price))
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
            print("canceled!")
            self.waitUntilServerReady()
            print(json_string, file=sys.stderr) 
            print(json_string, file=self.exchange)
            self.outstandingCancels.append(orderId)

def connect(serv_addr, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((serv_addr, int(port)))
    return (s, s.makefile('w+', 1))

#BUY means you get XLF
def convertXLF(direction, amount, p, exchange):
    orderID = p.nextOrderID
    p.nextOrderID += 1
    json_string = '{"type": "convert", "order_id": %d' % orderID + ', "symbol": "XLF", "dir": "' + direction + '", "size": %s}' % str(amount)
    print(json_string, file=sys.stderr)
    p.waitUntilServerReady()
    print(json_string, file=exchange)   
    p.orders[orderID] = Order("XLF", -1, amount, direction, p, isConvert = True)
    if direction == "BUY":
      sign = +1
    else:
      sign = -1
    p.positions["XLF"] += sign * amount
    p.positions["BOND"] -= sign * 3* amount/10
    p.positions["GS"] -= sign * 2 * amount/10
    p.positions["MS"] -= sign * 3 * amount/10
    p.positions["WFC"] -= sign * 2 * amount/10

def direction_xlf_forward():
    bestAmount=0
    besti=0
    sellPrice=0
    buyPrice=0
    for i in xrange(10,101, 10): 
      a,b=getTotalPrice("XLF",i,p,"SELL")

      # b=getTotalPrice("VALBZ",i,p,"BUY")
      c,d=getTotalPrice("WFC",i/10 * 2,p,"BUY")
      e,f = getTotalPrice("GS", i/10 *2,p, "BUY")
      h,k = getTotalPrice("MS", i/10 * 3, p, "BUY")
      w,z = getTotalPrice("BOND", i/10 *3,p, "BUY")
      # d=getTotalPrice("VALE",i,p,"SELL")
      val_bundle = c + e + h + w
      if b==0 or d==0 or f==0 or k==0 or z==0: continue
      if val_bundle-a>bestAmount:
        bestAmount= val_bundle -a
        besti=i
        sellPrice=b
        buyPrice= [d,f,k,z]
      # elif b-d>bestAmount:
      #   b-d=bestAmount
      #   besti=i
    print("bestAmount:"+str(bestAmount))
    print("besti:"+str(besti))
    print("sellPrice:"+str(sellPrice))
    print("buyPrice:"+str(buyPrice))
    return (bestAmount,besti,sellPrice,buyPrice)

def direction_xlf_backward():
    bestAmount=0
    besti=0
    sellPrice=0
    buyPrice=0
    for i in xrange(10,101, 10):
      a,b=getTotalPrice("XLF",i,p,"BUY")

      # b=getTotalPrice("VALBZ",i,p,"BUY")
      c,d=getTotalPrice("WFC",i/10 * 2,p,"SELL")
      e,f = getTotalPrice("GS", i/10 *2,p, "SELL")
      h,k = getTotalPrice("MS", i/10 * 3, p, "SELL")
      w,z = getTotalPrice("BOND", i/10 *3,p, "SELL")
      # d=getTotalPrice("VALE",i,p,"SELL")
      val_bundle = c + e + h + w
      if b==0 or d==0 or f==0 or k==0 or z==0: continue
      if a - val_bundle>bestAmount:
        bestAmount= a - val_bundle
        besti=i
        sellPrice= [d, f,k, z]
        buyPrice= b
      # elif b-d>bestAmount:
      #   b-d=bestAmount
      #   besti=i
    print("bestAmount:"+str(bestAmount))
    print("besti:"+str(besti))
    print("sellPrice:"+str(sellPrice))
    print("buyPrice:"+str(buyPrice))
    return (bestAmount,besti,sellPrice,buyPrice)

#direction is "BUY" or "SELL"
def orderSec(symbol, direction, price, amount, p, exchange):
    orderId = p.nextOrderID
    p.nextOrderID += 1
    json_string = '{"type": "add", "order_id": '+ str(orderId) + ',"symbol": "' + symbol +'", "dir": "' +  direction + '", "price": ' + str(price) + ', "size" : ' + str(amount) + '}'
    print(json_string, file=sys.stderr)
    p.waitUntilServerReady()
    print(json_string, file=exchange)   
    p.orders[orderId] = Order(symbol, price, amount, direction, p)

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

def convert(symbol,direction,size,p):
    orderID=p.nextOrderID
    p.nextOrderID += 1
    json_string = '{"type": "convert", "order_id": '+ str(orderID) + ',"symbol": "' + symbol +'", "dir": "' +  direction + '", "size" : ' + str(size) + '}'
    print(json_string, file=sys.stderr)
    p.waitUntilServerReady()
    print(json_string, file=p.exchange)   
    p.orders[orderID] = Order(symbol, 0, size, direction, p ,True)

          

def parseData(msg, p):
    print(p.balist)
    dat = json.loads(msg)
    if dat['type'] == "reject" and dat['error'] == "TRADING_CLOSED":
      sys.exit(2)
    elif dat['type'] == 'out':
        orderId = dat["order_id"]
        try:
          sym=p.orders[int(orderId)].symbol

          if p.currentBuyID[sym]==dat['order_id']: 
            json_string = '{"type": "cancel", "order_id": %s}' % p.currentSellID[sym]
            p.waitUntilServerReady()
            print(json_string, file=sys.stderr) 
            print(json_string, file=p.exchange)
            p.outstandingCancels.append(p.currentSellID[sym])

            orderSec(p.orders[orderId].symbol, "SELL", p.currentBuy[sym]+1, 5, p, p.exchange)
            p.currentBuy[sym]=0
            p.currentBuyID[p.orders[orderId].symbol]=-1
          elif p.currentSellID[sym]==dat['order_id']: 
              
              json_string = '{"type": "cancel", "order_id": %s}' % p.currentBuyID[sym]
              p.waitUntilServerReady()
              print(json_string, file=sys.stderr) 
              print(json_string, file=p.exchange)
              p.outstandingCancels.append(p.currentBuyID[sym])
              orderSec(p.orders[orderId].symbol, "BUY", p.currentBuy[sym]+1, 5, p, p.exchange)
              p.currentSellID[sym]=0
              p.currentSell[sym]=100000000000000
          # if orderId in p.balist:
          #   p.balist.remove(orderId)
          if orderId in p.outstandingCancels:
            p.outstandingCancels.remove(orderId)
            try:
              del p.orders[orderId]
            except:
              next
        except:
          next
    elif dat['type'] == 'ack':
        order = p.orders[dat['order_id']]
        if p.orders[dat['order_id']].isConvert==True:
            order.fill(p.orders[dat['order_id']].amount,p)
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
        p.buyList[sym]=[]
        p.sellList[sym]=[]
        for (val, size) in sell:
            p.sellList[sym].append([int(val),int(size)])
            if val < cheapSell:
              cheapSell = val
              cheapestSellAmt=size
        for (val, size) in buy:
            p.buyList[sym].append([int(val),int(size)])
            if val > highBuy:
              highBuy = val
              highestBuyAmt=size
        p.highestBuy[sym] = highBuy
        p.cheapestSell[sym] = cheapSell
        p.highestBuyAmt[sym]=highestBuyAmt
        p.cheapestSellAmt[sym] = cheapestSellAmt

    elif dat['type'] == "hello":
        syms = dat['symbols']
        for info in syms:
          theSym = info['symbol']
          position = info['position']
          p.positions[theSym] = position

def correctAmount1():
    bestAmount=0
    besti=0
    sellPrice=0
    buyPrice=0
    for i in xrange(1,11):
      a,b=getTotalPrice("VALBZ",i,p,"SELL")

      # b=getTotalPrice("VALBZ",i,p,"BUY")
      c,d=getTotalPrice("VALE",i,p,"BUY")
      # d=getTotalPrice("VALE",i,p,"SELL")
      
      if a-c>bestAmount:
        bestAmount=c-a
        besti=i
        sellPrice=b
        buyPrice=d
      # elif b-d>bestAmount:
      #   b-d=bestAmount
      #   besti=i
    return (bestAmount,besti,sellPrice,buyPrice)

def correctAmount2():
    bestAmount=0
    besti=0
    sellPrice=0
    buyPrice=0
    for i in xrange(1,11):
      # a=getTotalPrice("VALBZ",i,p,"SELL")
      b,c=getTotalPrice("VALBZ",i,p,"BUY")
      # c=getTotalPrice("VALE",i,p,"BUY")
      d,e=getTotalPrice("VALE",i,p,"SELL")
      
      
      if d-b>bestAmount:
        bestAmount=b-d
        besti=i
        sellPrice=e
        buyPrice=c
    return (bestAmount,besti,sellPrice,buyPrice)


def getTotalPrice(sym,amount,p,dir):
    totalPrice=0
    totalAmount=0
    finalPrice=0
    if dir=="BUY": 
      l=p.buyList
    else: 
      l=p.sellList
    for (val,size) in l[sym]:
      if totalAmount>= amount:
        break
      if totalAmount+size<amount:
        totalAmount+=size
        totalPrice+=(val*size)
      elif totalAmount+size>=amount:
        totalAmount=amount
        totalPrice+=(amount-totalAmount)*val
        finalPrice=val
    return (totalPrice,finalPrice)


def main():
    alpha=0.5
    if len (sys.argv) != 3: 
      print ("feed server address as argument!")
      sys.exit(2)
    s, exchange = connect(sys.argv[1],sys.argv[2])

    json_string = '{"type": "hello", "team":"CUPCAKELY"}'
    print(json_string, file=exchange)
    hello_from_exchange = exchange.readline().strip()
    print("The exchange replied: %s" % str(hello_from_exchange),file = sys.stderr)
    
    global p
    p = Portfolio(exchange)
    parseData(hello_from_exchange, p)

    print("entering main loop", file = sys.stderr)
   
    disableBOND = True
    disableVale = True
    disableXLF = True
    disableValeArbitrage =True
    disableBundleArbitrage=True
    disablePennyPitching=False
    disableEquityMidTrading=True

  
    price_VALE=0
    numRound=0
    while True:
      message = exchange.readline().strip()
      dat=json.loads(message)
      parseData(message, p)

      if not disableEquityMidTrading: 

        mean_value_gs = int(round(p.cheapestSell["GS"] + p.highestBuy["GS"])/2.0) 
        mean_value_ms = int(round(p.cheapestSell["MS"] + p.highestBuy["MS"])/2.0)
        mean_value_wfc = int(round(p.cheapestSell["WFC"] + p.highestBuy["WFC"])/2.0)

        print("setting GS order at:" + str(mean_value_gs))
        print("setting MS order at:" + str(mean_value_ms))
        print("setting WFC order at:"+str(mean_value_wfc))

        p.CancelObsoleteOrders("GS", mean_value_gs, 1)
        p.CancelObsoleteOrders("MS", mean_value_ms, 1)
        p.CancelObsoleteOrders("WFC", mean_value_wfc, 1)

        orderSec("GS", "BUY", mean_value_gs-1, 5, p, exchange)
        orderSec("GS", "SELL", mean_value_gs+1, 5, p, exchange)

        orderSec("MS", "BUY", mean_value_ms-1, 5, p, exchange)
        orderSec("MS", "SELL", mean_value_ms+1, 5, p, exchange)

        orderSec("WFC", "BUY", mean_value_wfc-1, 5, p, exchange)
        orderSec("WFC", "SELL", mean_value_wfc+1, 5, p, exchange)
        
          
      if not disablePennyPitching:
          symbols=["BOND","VALBZ","VALE","GS","MS","WFC","XLF"]
          
          for s in symbols:

              # if p.highestBuy[s]==p.cheapestSell[s]-1:
              #   if p.highestBuy[s]>p.currentBuy:
              #     json_string = '{"type": "cancel", "order_id": %s}' % p.currentBuyID
              #     p.waitUntilServerReady()
              #     print(json_string, file=sys.stderr) 
              #     print(json_string, file=p.exchange)
              #     p.outstandingCancels.append(p.currentBuyID)

              #     orderSec(s, "BUY", p.highestBuy[s], 1, p, exchange)
              #     p.currentBuyID=p.nextOrderID-1
              #     p.currentBuy=p.highestBuy[s]
              #     print("add in 1")
              #     print("now currentbuy is" + str(p.currentBuy) + "highestBuy is" + str(p.highestBuy[s]))
              #     print("now currentsell is" + str(p.currentSell) + "highestSell is" + str(p.cheapestSell[s]))

              #   if p.cheapestSell[s]<p.currentSell:
              #     json_string = '{"type": "cancel", "order_id": %s}' % p.currentSellID
              #     p.waitUntilServerReady()
              #     print(json_string, file=sys.stderr) 
              #     print(json_string, file=p.exchange)
              #     p.outstandingCancels.append(p.currentBuyID)
              #     orderSec(s, "SELL", p.cheapestSell[s], 1, p, exchange)  
              #     p.currentSellID=p.nextOrderID-1
              #     p.currentSell=p.cheapestSell[s]
              #     print("add in 2")
              #     print("now currentbuy is" + str(p.currentBuy) + "highestBuy is" + str(p.highestBuy[s]))
              #     print("now currentsell is" + str(p.currentSell) + "highestSell is" + str(p.cheapestSell[s]))
              if p.highestBuy[s]<=p.cheapestSell[s]-2:
                if p.highestBuy[s]>p.currentBuy[s]:

                  json_string = '{"type": "cancel", "order_id": %s}' % p.currentBuyID[s]
                  p.waitUntilServerReady()
                  print(json_string, file=sys.stderr) 
                  print(json_string, file=p.exchange)
                  p.outstandingCancels.append(p.currentBuyID[s])

                  orderSec(s, "BUY", p.highestBuy[s]+1, 1, p, exchange)
                  p.currentBuyID[s]=p.nextOrderID-1
                  p.currentBuy[s]=p.highestBuy[s]+1
                  print("add in 3")
                  
                
                if p.cheapestSell[s]<p.currentSell[s]:
                  json_string = '{"type": "cancel", "order_id": %s}' % p.currentSellID[s]
                  p.waitUntilServerReady()
                  print(json_string, file=sys.stderr) 
                  print(json_string, file=p.exchange)
                  p.outstandingCancels.append(p.currentBuyID[s])

                  orderSec(s, "SELL", p.cheapestSell[s]-1, 1, p, exchange)  
                  p.currentSellID[s]=p.nextOrderID-1
                  p.currentSell[s]=p.cheapestSell[s]-1
                  print("add in 4")
                  
                  
      
      if not disableBundleArbitrage:
          numRound=0
          bestAmount1,besti1,sellPrice1,buyPrice1 = direction_xlf_forward()
          bestAmount2,besti2,sellPrice2,buyPrice2 = direction_xlf_backward()
          portfolio=p
          #(wfc, gs, ms, bond)
          if bestAmount1 > 100 and sellPrice1!=0 and buyPrice1!=[0,0,0,0] and besti1!=0 and len(p.balist)==0:
            
            print("the best amount is:" + str(bestAmount1))
            amountToTrade = besti1
            orderSec("XLF", "BUY", sellPrice1, amountToTrade, portfolio, exchange)
            p.balist.add(p.nextOrderID-1)
            convert("XLF", "SELL", amountToTrade, portfolio)
            p.balist.add(p.nextOrderID-1)
            orderSec("WFC", "SELL", buyPrice1[0], amountToTrade, portfolio, exchange)
            p.balist.add(p.nextOrderID-1)
            orderSec("GS", "SELL", buyPrice1[1], amountToTrade, portfolio, exchange)
            p.balist.add(p.nextOrderID-1)
            orderSec("MS", "SELL", buyPrice1[2], amountToTrade, portfolio, exchange)
            p.balist.add(p.nextOrderID-1)
            orderSec("BOND", "SELL", buyPrice1[3], amountToTrade, portfolio, exchange)
            p.balist.add(p.nextOrderID-1)


          elif bestAmount2 > 100 and buyPrice2!=0 and sellPrice2!=[0,0,0,0] and besti2!=0 and len(p.balist)==0:
            print("the best amount is:" + str(bestAmount2))
            
            amountToTrade = besti2
            orderSec("WFC", "BUY", sellPrice2[0], amountToTrade, portfolio, exchange)
            p.balist.add(p.nextOrderID-1)
            orderSec("GS", "BUY", sellPrice2[1], amountToTrade, portfolio, exchange)
            p.balist.add(p.nextOrderID-1)
            orderSec("MS", "BUY", sellPrice2[2], amountToTrade, portfolio, exchange)
            p.balist.add(p.nextOrderID-1)
            orderSec("BOND", "BUY", sellPrice2[3], amountToTrade, portfolio, exchange)
            p.balist.add(p.nextOrderID-1)
            convert("XLF", "BUY", amountToTrade, portfolio)
            p.balist.add(p.nextOrderID-1)
            orderSec("XLF", "SELL", buyPrice2, amountToTrade, portfolio, exchange)
            p.balist.add(p.nextOrderID-1)

      if not disableBOND:
        market_making(exchange) 

      if not disableValeArbitrage:
        bestAmount1,amountToTrade1,sellPrice1,buyPrice1=correctAmount1()
        bestAmount2,amountToTrade2,sellPrice2,buyPrice2=correctAmount2()
        if bestAmount1>10:
            amountToTrade=amountToTrade1
            orderSec("VALBZ","BUY",sellPrice1, amountToTrade , p,exchange)
            convert("VALE","BUY",amountToTrade,p)
            orderSec("VALE","SELL",buyPrice1, amountToTrade , p,exchange)
        elif bestAmount2>10:
            amountToTrade=amountToTrade2
            orderSec("VALE","BUY",sellPrice2, amountToTrade , p,exchange)
            convert("VALE","SELL",amountToTrade,p)
            orderSec("VALBZ","SELL",buyPrice2, amountToTrade , p,exchange)

      
      if not disableVale:
        if  p.highestBuy["VALBZ"] != 0 and p.cheapestSell["VALBZ"] !=0:
            #use EMA as the fair price
            price_VALE=int(round((p.highestBuy["VALBZ"] + p.cheapestSell["VALBZ"])/2.0))
            p.CancelObsoleteOrders("VALE", price_VALE, p.halfSpread["VALE"])
            tradeSymbol("VALE", exchange, price_VALE, p.halfSpread["VALE"], p)
      
      if not disableXLF: 
        if p.highestBuy['GS'] != 0 and p.cheapestSell['GS']!=0 and p.highestBuy['MS'] !=0 and p.cheapestSell['MS'] !=0 and p.highestBuy['WFC'] !=0 and p.cheapestSell['WFC'] !=0 and p.cheapestSell['XLF'] != 0 and p.highestBuy['XLF'] != 0:
          price_WFC = int(round((p.highestBuy['WFC']+  p.cheapestSell['WFC'])/2.0))
          price_MS = int(round((p.highestBuy['MS']+  p.cheapestSell['MS'])/2.0))
          price_XLF = int(round((p.highestBuy['XLF']+  p.cheapestSell['XLF'])/2.0))
          price_GS = int(round((p.highestBuy['GS']+  p.cheapestSell['GS'])/2.0))
          p.xlfguess = (3 * 1000 + 2 * price_GS + 3 * price_MS + 2 * price_WFC)
          p.xlfguess = int(round(p.xlfguess / 10.0))

          amount = 40

          longAmount  = p.positions["XLF"] + p.OutstandingOrders("XLF", "BUY")
          shortAmount = -1 * p.positions["XLF"] + p.OutstandingOrders("XLF", "SELL")

          if abs(p.xlfguess - price_XLF) > 100/amount + 10:
            
            if p.xlfguess < price_XLF:
              direction = "BUY"
            else:
              direction = "SELL"
            
            if (direction == "BUY" and amount + longAmount < 100) or (direction == "SELL" and amount + shortAmount < 100):
              netDirection = ("BUY" if direction == "SELL" else "SELL")
              orderSec("XLF", netDirection, price_XLF + p.halfSpread["XLF"], amount, p, exchange)
              orderSec("GS", direction, price_GS, amount/10 * 2, p, exchange)
              orderSec("MS", direction, price_MS, amount/10 * 3, p, exchange)
              orderSec("WFC", direction, price_WFC, amount/10 * 2, p, exchange)
             
              convertXLF(direction, amount, p, exchange)

              print("xlfguess: %d price_xlf: %d" % (p.xlfguess, price_XLF), file=sys.stderr)
          #p.CancelObsoleteOrders("XLF", p.xlfguess, p.halfSpread["XLF"])
          #tradeSymbol("XLF", exchange, p.xlfguess, p.halfSpread["XLF"], p)              

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
