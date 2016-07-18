if not disableEquityMidTrading: 

        mean_value_gs = int(round(p.highestBuy["GS"] - p.highestSell["GS"])/2.0) 
        mean_value_ms = int(round(p.highestBuy["MS"] - p.highestSell["MS"])/2.0)
        mean_value_wfc = int(round(p.highestBuy["WFC"] - p.highestSell["WFC"])/2.0)

        orderSec("GS", "BUY", mean_value_gs-1, 5, p, exchange)
        orderSec("GS", "SELL", mean_value_gs+1, 5, p, exchange)

        orderSec("MS", "BUY", mean_value_ms-1, 5, p, exchange)
        orderSec("MS", "SELL", mean_value_ms+1, 5, p, exchange)

        orderSec("WFC", "BUY", mean_value_wfc-1, 5, p, exchange)
        orderSec("WFC", "SELL", mean_value_wfc+1, 5, p, exchange)