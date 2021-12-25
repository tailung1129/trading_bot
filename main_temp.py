from numpy import string_
import requests
import mysql.connector
import threading
import datetime
import time
import ccxt
import ccxtpro
import asyncio
from requests import api
from requests.models import Response
try:
    from urllib import urlencode
# python3
except ImportError:
    from urllib.parse import urlencode
from app.BinanceAPI import BinanceAPI
from app.Database import Database
from rsiCalc import rsiFunc
# from client_trade import client_trade

arraycoins = ["BTC","ETH","BCH","XRP","EOS","LTC","TRX","ETC","LINK","XLM","ADA","XMR","DASH","ZEC","XTZ","BNB","ATOM","ONT","IOTA","BAT","VET","NEO","QTUM","IOST","THETA","ALGO","ZIL","KNC","ZRX","COMP","OMG","DOGE","SXP","KAVA","BAND","RLC","WAVES","MKR","DOT","YFI","BAL","CRV","TRB","YFII","RUNE","SUSHI","SRM","BZRX","EGLD","SOL","ICX","STORJ","BLZ","UNI","AVAX","FTM","HNT","ENJ","FLM","TOMO","REN","KSM","NEAR","AAVE","FIL","RSR","LRC","MATIC","OCEAN","CVC","BEL","CTK","ALPHA","ZEN","SKL","GRT","1INCH","AKRO","CHZ","SAND","ANKR","LUNA","BTS","LIT","UNFI","DODO","REEF","RVN","SFP","XEM","COTI","CHR","MANA","ALICE","HBAR","ONE","LINA","STMX","DENT","CELR","HOT","MTL","OGN","BTT","SC","AXS","NKN","SNX","DGB","ICP","BAKE","GTC","KEEP","TLM","IOTX","AUDIO","RAY","AR","ATA","C98","CELO","DYDX","GALA","MASK","1000SHIB","1000XEC","BTCDOM","DEFI","KLAY"]
#arraycoins = ["BTC","ETH","BCH","XRP","EOS","LTC"]
client = BinanceAPI()
trade_open_list = []
trade_cnt = 0

bin_features = mysql.connector.connect(
	host="92.205.3.110",
	user="crypto_feauters_test",
	password="crypto_feauters_test",
	database="binancefutures",
)
global_param = Database.get_global_parameters(bin_features)
param_trailing_start_perc = float(global_param[22][1])
change_sl = param_trailing_start_perc

def binance_order(symbol, openpostion, ordertype):
	bin_features = mysql.connector.connect(
		host="92.205.3.110",
		user="crypto_feauters_test",
		password="crypto_feauters_test",
		database="binancefutures",
	)
	coin_full = symbol
	coin_abr = coin_full[:-4]
	try:
		clients = Database.get_clients(bin_features)
	except:
		return
	print('order', coin_full)
	for data in clients:
		# trade = client_trade
		fixedamount = 0
		client_email = data[1]
		client_isfuture = data[7]
		leverage = int(data[5])
		spotamount = float(data[6])
		apikey = data[3]
		secretkey = data[4]
		fixedamount = spotamount * leverage
		if len(apikey) > 10 and len(secretkey) > 10:
			if float(client_isfuture) == float(1):
				print("The trade of Client %s" % client_email)
				binance = ccxt.binance({
					"apiKey":apikey,
					"secret": secretkey,
					# "apiKey":"NGKVf4rdsSVULydWsknBkOWQ2kys3IgdvoyM8oY0zavTMJIbjr5O7y4HDXUBmMcp",
					# "secret": "7CfZ3SO9zCJHDavcwreUA2ohkWhApkZxEcrWDTtpJHdusc9IIvw4wsjwPFqysfxM",
					"options": {"defaultType": "future", 'adjustForTimeDifference' : True},
					"timeout": 60000,
					"enableRateLimit": True,
				})
				try:
					objsym = client.get_price(coin_full)
				except Exception as e:
					print("api error : ", e)
					return
				try:
					curpice = float(objsym['price'])
					fixedamount = float(fixedamount) * 1. / curpice
					binance.load_markets()

					binance.verbose = False
					balance = binance.fetch_balance()
					if openpostion == 1:
						params = {
							'symbol' : coin_full,
							'leverage' : leverage,
							'recvWindow' : 50000
						}
						free_balance = float(balance['info']['maxWithdrawAmount'])						
						if(free_balance > spotamount):
							symbol = "%s/USDT" % coin_abr
							print("opensymbol", symbol)
							print("openordertype", ordertype)
							print("openfixedamount", fixedamount)
							print("openparams", params)
							binance.fapiPrivate_post_leverage(params)
							binance.create_order(symbol, "MARKET", ordertype, fixedamount, None, params)
						
					elif openpostion == 2:
						params = {
							# 'symbol' : coin_full,
							# 'leverage' : leverage,
							# 'recvWindow' : 50000,
							'reduceOnly' : 'true'
						}
						position = balance['info']['positions']
						posamt = 0
						for pos in position:
							if(pos['symbol'] == coin_full):
								posamt = abs(pos['positionAmt'])
						if(ordertype == 'BUY'):
							rev = 'SELL'
						else:
							rev = 'BUY'
						symbol = "%s/USDT" % coin_abr
						print("closesymbol", symbol)
						print("closeordertype", rev)
						print("closefixedamount", posamt)
						print("closeparams", params)
						binance.fapiPrivate_post_leverag(params)
						binance.create_order(symbol,"MARKET", rev, posamt, None,params)		
				except Exception as e:
					print('there is exception : ',e)
					return

def get_or_create_eventloop():
	try:
		return asyncio.get_event_loop()
	except RuntimeError as ex:
		if "There is no current event loop in thread" in str(ex):
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
			return asyncio.get_event_loop()
def table(values):
    first = values[0]
    keys = list(first.keys()) if isinstance(first, dict) else range(0, len(first))
    widths = [max([len(str(v[k])) for v in values]) for k in keys]
    string = ' | '.join(['{:<' + str(w) + '}' for w in widths])
    return "\n".join([string.format(*[str(v[k]) for k in keys]) for v in values])

async def ohlc(exchange, coin):
	#future = asyncio.Future()
	exchange = ccxtpro.binance({'enableRateLimit': True})
	ohlcvs= await exchange.watch_ohlcv(coin, '1h', None,10)
	print(table([[exchange.iso8601(o[0])] + o[1:] for o in ohlcvs]))
	#response = await exchange.watch_ohlcv('ADA/USDT', '1h', 500, params={'price':'index'})
	#return response
	#print(future.result())

#Thread function for coin
def coin_thread(i):
	# print(i)
	global trade_open_list
	binance_features = mysql.connector.connect(
		host="92.205.3.110",
		user="crypto_feauters_test",
		password="crypto_feauters_test",
		database="binancefutures",
	)
	coin_abr = i
	coin_full = "%sUSDT" % coin_abr
	try:
		td_close = Database.get_flag_orders(coin_full, binance_features)	
	except:
		return
	if td_close:
		coin_close_abr = td_close[1]
		order_flag = td_close[9]
		try:
			Database.close_order_finally(coin_close_abr, binance_features)
		except:
			return
		binance_order(coin_close_abr, 2, order_flag)
	else :
		try:
			tradeopenexist = Database.trade_openandexist(coin_full, binance_features)
		except:
			return
		if tradeopenexist[0] > 0:
			return
	# RSI Calculate and get LastVal
	try:
		loop = get_or_create_eventloop()
		symbol = f"{coin_abr}/USDT"
		loop.run_until_complete(ohlc(symbol))
		loop.close()
		return
	except Exception as e:
		print(f"this is exception : {e}")
		return

	try:
		closes = []
		for ind in data:
			if ind == None:
				return
			temp = float(ind[1])
			closes.append(temp)
	except Exception as e:
		print(f"There is exception : {e}")
		return
	clsarray = rsiFunc(closes, rsi_period)
	lastval = clsarray[len(clsarray)-1]
	buysell_flag = 0
	if(lastval <= rsi_buy):
		buysell_flag = 1
		order_type = "BUY"
	elif(lastval >= rsi_sell):
		buysell_flag = 2
		order_type = "SELL"
	else:
		return
	data = client.get_klines_v1(coin_full, changeper_timeframe, 1)
	changeper_ = 0
	changeper_ = float(data[0][4]) * 100. / float(data[0][1])
	if(changeper_ >= 100.):
		changeper_ -= 100.
	else:
		changeper_ = -(100. - changeper_)
	if (buysell_flag == 1 and ((changeper_ > 0 and changeper_ >= min__change) or min__change == 0)) or (buysell_flag == 2 and ((changeper_ < 0 and changeper_ <= min__change) or min__change == 0)):	
		marketprice = client.get_price(coin_full)
		marketprice = float(marketprice['price'])
		try:
			cn_digits = Database.get_coindigit(coin_abr, binance_features)
			cn_digits = int(cn_digits[0])
		except:
			co_digits = 2
		# OpenTrade	- Orders start for clients
		if(buysell_flag == 1):
			trade_sl = round(((100. - param_default_sl_perc) * marketprice ) / 100., cn_digits)
			trade_tp = round(((100. + param_default_tp_perc) * marketprice ) / 100., cn_digits)
		else:
			trade_tp = round(((100. - param_default_tp_perc) * marketprice ) / 100., cn_digits)
			trade_sl = round(((100. + param_default_sl_perc) * marketprice ) / 100., cn_digits)
		current_time = int(time.time())
		trade_open_list.append([coin_full, 1, marketprice, 0, current_time, 0, 0, None, order_type, cn_digits, 100, trade_sl, trade_tp, None, 'ROBOTNOTHAND', None, None])
		
def all_opentrades_check():
	bin_features = mysql.connector.connect(
		host="92.205.3.110",
		user="crypto_feauters_test",
		password="crypto_feauters_test",
		database="binancefutures",
	)
	try:
		global_param = Database.get_global_parameters(bin_features)
		open_trades = Database.trade_all_openandexist(bin_features)
	except:
		return

	max_loss_per = float(global_param[7][1])
	max_profit_per = float(global_param[8][1])
	param_trailing_start_perc = float(global_param[22][1])
	param_trailing_perc = float(global_param[23][1])
	cumuusd = 0
	trade_close_data = []
	for data in open_trades:
		trade_id = data[0]
		symbol = data[1]
		leverage = data[2]
		entryprice = float(data[3])
		ordertype = data[9]
		amount = data[11]
		try:
			objsym = client.get_price(symbol)
			closedprice = float(objsym['price'])
		except:
			continue
		current_time = int(time.time())
		if	ordertype == "BUY":
			reversedentry = entryprice - closedprice
			perc = ((reversedentry * 100) / closedprice ) * leverage
			profitnusd = perc * amount / 100
			if(reversedentry > 0):
				profitnusd = -(abs(profitnusd))
				profitnusd_db = profitnusd
			else:
				profitnusd = abs(profitnusd)
				profitnusd_db = 2 * profitnusd
			trade_close_data.append([trade_id, profitnusd_db, closedprice, current_time, symbol, ordertype])
			cumuusd = cumuusd + profitnusd
		elif ordertype == 'SELL':
			reversedentry = closedprice - entryprice
			perc = ((reversedentry * 100) / entryprice) * leverage
			profitnusd = perc * amount / 100
			if(reversedentry > 0):
				profitnusd = -abs(profitnusd)
				profitnusd_db = profitnusd
			else:
				profitnusd = abs(profitnusd)
				profitnusd_db = 2 * profitnusd
			trade_close_data.append([trade_id, profitnusd_db, closedprice, current_time, symbol, ordertype])
			cumuusd = cumuusd + profitnusd
	global change_sl
	if (cumuusd <= change_sl) and (change_sl != param_trailing_start_perc):
		for temp in trade_close_data:
			binance_order(temp[4], 2, temp[5])
			try:
				Database.update_trade(temp[0], temp[1], temp[2], temp[3], bin_features)
			except:
				continue
		# freezing time -- search this text
		print("------------------------------------------------------->","max-percent", cumuusd)
		print("total_sl", change_sl)
		print("*** Trades Closed by Trailing Stop ***")
		change_sl = param_trailing_start_perc
		x = 60 * 10 # 5min - 300s
		time.sleep(x)
	elif(cumuusd > max_profit_per):
		change_sl = cumuusd - param_trailing_perc
		print("------------------------------------------------------->","max-percent", cumuusd)
		print("total_sl", change_sl)
		print("********************* TRAILING *************************")
	elif(cumuusd <= -(max_loss_per)):
		for temp in trade_close_data:
			binance_order(temp[4], 2, temp[5])
			try:
				Database.update_trade(temp[0], temp[1], temp[2], temp[3], bin_features)
			except:
				continue

		# freezing time -- search this text
		print("------------------------------------------------------->","max-percent", cumuusd)
		print("*** Trades Closed - STOP LOSS ***")
		x = 60 * 10 # 5min - 300s
		time.sleep(x)
	else:
		print("------------------------------------------------------->","max-percent", cumuusd)
		print("total_sl", change_sl)
#Threads start for coin-arrays ---Main Thread
while(True):
	#global parameters
	all_opentrades_check()
	bin_features = mysql.connector.connect(
		host="92.205.3.110",
		user="crypto_feauters_test",
		password="crypto_feauters_test",
		database="binancefutures",
	)
	try:
		if client.ping():
			time.sleep(20)
	except:
		pass
	#loop = get_or_create_eventloop()	
	#loop.run_until_complete(ohlc(exchange, 'ADA/USDT'))

	#loop.run_until_complete(ohlc(exchange, 'BTC/USDT'))
	try:
		global_param = Database.get_global_parameters(bin_features)
		count = Database.trade_openandexistcount(bin_features)
		count = count[0]
	except:
		time.sleep(30)
	print('-------------------------> Open Trades', count)
	if(count > 0):
		all_opentrades_check()
	MAX_TRADES = int(global_param[4][1])
	enable_robot = global_param[5][1]
	if(enable_robot == 'false'):
		print("Bot is disabled!")
		break
	max_loss_per = float(global_param[7][1])
	max_profit_per = float(global_param[8][1])
	freee_profit = int(global_param[9][1])
	freee_loss = int(global_param[10][1])
	freee_close_all = int(global_param[11][1])
	freee_until = float(global_param[12][1])
	rsi_period = int(global_param[13][1])
	rsi_timeframe = global_param[14][1]
	rsi_buy = float(global_param[15][1])
	rsi_sell = float(global_param[16][1])
	min__change = float(global_param[17][1])
	changeper_timeframe = global_param[19][1]
	param_default_sl_perc = float(global_param[20][1])
	param_default_tp_perc = float(global_param[21][1])
	param_trailing_start_perc = float(global_param[22][1])
	param_trailing_perc = float(global_param[23][1])
	thread_actions = []
	trade_open_list = []
	exchange = ccxtpro.binance()
	if(count != MAX_TRADES):
		for i in arraycoins:
			thread = threading.Thread(target=coin_thread, args=(i,))
			thread_actions.append(thread)
			thread.start()
		for thread_ in thread_actions:
			thread_.join()	
	else:
		try:	
			open_trades = Database.trade_all_openandexist(bin_features)
			for data in open_trades:
				coin_abr = data[1][:-4]
				thread = threading.Thread(target=coin_thread, args=(coin_abr,))
				thread_actions.append(thread)
				thread.start()
			for thread_ in thread_actions:
				thread_.join()	
		except:
			break
	for data in trade_open_list:
		count = count + 1
		if(count <= MAX_TRADES):
			try:
				binance_order(data[0], 1, data[8])
				Database.write(data, bin_features)
			except:
				pass
		else:
			print("There are MAX trades!")
			break
	if count > 0:
		all_opentrades_check()
	time.sleep(5)

		


