import json

''''
def scan_object(object):
	if object["type"]:
		type_l.append(object["type"])
	if object["order_id"]:
		type_l.append(object["order_id"])
	if object["symbol_l"]:
		type_l.append(object["symbol_l"])
	if object["price_l"]:
		type_l.append(object["price_l"])
	if object["size_l"]:
		type_l.append(object["size_l"])
'''

def open(exchange):
		j = json.loads(exchange)
		return j["symbols"] if j["type"] == "open" else []
	
def close(exchange):
		j = json.loads(exchange)
		return j["symbols"] if j["type"] == "close" else []

def getPrices(exchange,sym, dir):
		j = json.loads(exchange)
		if j["type"] == "book" and j["sym"] == "sym":
			return j["buy"] if dir == "BUY" else j["sell"]
	
def fill(exchange):
	l = json.loads(exchange):
		dictionary={}
		if l["type"] == "fill":
			dictionary["order_id"] = l["order_id"]
			dictionary["symbol"] = l["symbol"]
			dictionary["dir"] = l["dir"]
			dictionary["price"] = l["price"]
			dictionary["size"] = l["size"]
			return dictionary

def out(exchange):
	l = json.loads(exchange)
	return l["order_id"] if l["type"] == "out" else []


def reject(exchange):
	l = json.loads(exchange)
	dictionary = {}
	if l["type"] == "reject":
		dictionary["order_id"] = l["order_id"]
		dictionary["error"] = l["error"]
		return dictionary

def ack(exchange):
	l = json.loads(exchange)
	return l["order_id"] if l["type"] == "ack" else []

def trade(exchange):
	l = json.loads(exchange)
	dictionary = {}
	if l["type"] == "trade":
		dictionary["symbol"] = l["symbol"]
		dictionary["price"] = l["price"]
		dictionary["size"] = l["size"]
		return dictionary

def error(exchange):
	l = json.loads(exchange)
	return l["error"] if l["type"] == "error" else []

def cloudsell(portfolio):
	#dictionaries
	p_h_value = portfolio.highestBuy
	p_c_value = portfolio.cheapestSell

	val_security_h_bundle = 3*p_h_value["BOND"] + 2*p_h_value["GS"] + 3*p_h_value["MS"] + 2*p_h_value["WFC"]
	val_security_it_c = 10 * p_c_value["XLF"]

	## reverse

	val_security_c_bundle = 3*p_c_value["BOND"] + 2*p_c_value["GS"] + 3*p_c_value["MS"] + 2*p_c_value["WFC"]
	val_security_it_h = 10 * p_h_value["XLF"]

	#compare 

	if val_security_c_bundle + 100 < val_security_it_h:
		amountToTrade = min(portfolio.cheapestSellAmt["XLF"], portfolio.highestBuyAmt["BOND"], portfolio.highestBuyAmt["MS"], portfolio.highestBuyAmt["WFC"], portfolio.highestBuyAmt["GS"])
		orderSec("XLF", "BUY", p.cheapestSell["XLF"], amountToTrade, portfolio, exchange)
		convert("XLF", "BUY", amountToTrade, portfolio)
		orderSec("BOND", "SELL", p.highestBuy["BOND"], amountToTrade, portfolio, exchange)
		orderSec("GS", "SELL", p.highestBuy["GS"], amountToTrade, portfolio, exchange)
		orderSec("MS", "SELL", p.highestBuy["MS"], amountToTrade, portfolio, exchange)
		orderSec("WFC", "SELL", p.highestBuy["WFC"], amountToTrade, portfolio, exchange)

	if val_security_it_c + 100 < val_security_h_bundle:
		amountToTrade = min(portfolio.cheapestSellAmt["XLF"], portfolio.highestBuyAmt["BOND"], portfolio.highestBuyAmt["MS"], portfolio.highestBuyAmt["WFC"], portfolio.highestBuyAmt["GS"])
		orderSec("BOND", "BUY", p.highestBuy["BOND"], amountToTrade, portfolio, exchange)
		orderSec("GS", "BUY", p.highestBuy["GS"], amountToTrade, portfolio, exchange)
		orderSec("MS", "BUY", p.highestBuy["MS"], amountToTrade, portfolio, exchange)
		orderSec("WFC", "BUY", p.highestBuy["WFC"], amountToTrade, portfolio, exchange)
		convert("XLF", "SELL", amountToTrade, portfolio)






		
