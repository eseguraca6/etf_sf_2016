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





