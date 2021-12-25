# -*- coding: UTF-8 -*-
import mysql.connector

# binance_features = mysql.connector.connect(
# 	host="localhost",
# 	user="root",
# 	password="",
# 	database="binfutures",
# )

class Database():
         
    # Database (Todo: Not complated)
    @staticmethod
    def write(data, binance_features):
        '''    
        Save order
        data = orderid,symbol,amount,price,side,quantity,profit
        Create a database connection
        '''
        temp = []       
        for tmp in data:
            if tmp == None:
                tmp = 'NULL'
            temp.append(tmp)
        cur = binance_features.cursor()
        cur.execute("INSERT INTO test_trades (trade_symbol, trade_leverage, trade_entryprice, trade_closedprice, trade_openedat, trade_closedat, trade_profit, trade_hash, trade_type, trade_coin_digits, trade_amount, trade_sl, trade_tp, trade_closereasons, trade_by, trade_estimatedloss, trade_estimatedprofit) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % (temp[0], temp[1], temp[2], temp[3], temp[4], temp[5], temp[6], temp[7], temp[8], temp[9], temp[10], temp[11], temp[12], temp[13], temp[14], temp[15], temp[16]))
        cur.close()
        binance_features.commit()

    @staticmethod
    def update_trade(trade_id, profitnusd_db, closedprice, current_time, bin_features):
        cur = bin_features.cursor()
        cur.execute("update test_trades set trade_closedprice = '%s', trade_closedat= '%s',trade_profit = '%s', trade_closereasons='CLOSEDBYPROVIDER' where trade_id='%s'" % (closedprice, current_time, profitnusd_db, trade_id))
        cur.close()
        bin_features.commit()
    
    @staticmethod
    def read(orderid, binance_features):
        '''
        Query order info by id
        :param orderid: the buy/sell order id
        :return:
        '''
        cur = binance_features.cursor()
        cur.execute('SELECT * FROM orders WHERE orderid = ?', (orderid,))

        return cur.fetchone()
    
    @staticmethod
    def get_coin_array(binance_features):
        coin_array = "SELECT coin_abr from coin_name where coin_isvisible = 1"
        binance_cursor = binance_features.cursor()
        binance_cursor.execute(coin_array)
        coin_array = binance_cursor.fetchall()
        binance_cursor.close()
        return coin_array

    @staticmethod
    def get_global_parameters(binance_features):
        global_query = "SELECT param_name, param_value from global_parameters"
        binance_cursor = binance_features.cursor()
        binance_cursor.execute(global_query)
        global_parameters = binance_cursor.fetchall()      
        binance_cursor.close()      
        return global_parameters

    @staticmethod
    def trade_openandexistcount(binance_features):
        query = "select count(trade_id) from test_trades where trade_by = 'ROBOTNOTHAND' and   trade_closedat = 0 "
        binace_cursor = binance_features.cursor()
        binace_cursor.execute(query)
        count = binace_cursor.fetchone()
        return count

    @staticmethod
    def trade_all_openandexist(binance_features):
        query = "select * from test_trades where trade_by = 'ROBOTNOTHAND' and   trade_closedat = 0 "
        binace_cursor = binance_features.cursor()
        binace_cursor.execute(query)
        data = binace_cursor.fetchall()
        binace_cursor.close()
        return data

    @staticmethod
    def trade_openandexist(symbol, binance_features):
        query = "select count(trade_id) from test_trades where trade_symbol = '%s' and trade_by = 'ROBOTNOTHAND' and   trade_closedat = 0" % symbol
        binace_cursor = binance_features.cursor()
        binace_cursor.execute(query)
        is_exist = binace_cursor.fetchone()
        binace_cursor.close()
        return is_exist

    @staticmethod
    def trade_opendata(symbol, binance_features):
        query = "select * from test_trades where trade_symbol = '%s' and trade_by = 'ROBOTNOTHAND' and   trade_closedat = 0" % symbol
        binace_cursor = binance_features.cursor()
        binace_cursor.execute(query)
        data = binace_cursor.fetchone()
        binace_cursor.close()
        return data
    @staticmethod
    def get_coindigit(symbol, binance_features):
        query = "select coin_digits from coin_name where coin_abr = '%s'" % symbol
        binace_cursor = binance_features.cursor()
        binace_cursor.execute(query)
        cn_digits = binace_cursor.fetchone()
        binace_cursor.close()
        return cn_digits

    @staticmethod
    def get_clients(binance_features):
        query = "select client_id, client_email, client_pass, binance_apikey, binance_secretkey, binance_leverage, binance_lotamountpertrade,client_isfutures,client_regularbinance from tbl_client where client_enablefutures = '1'"
        binace_cursor = binance_features.cursor()
        binace_cursor.execute(query)
        client_data = binace_cursor.fetchall()
        binace_cursor.close()
        return client_data

    @staticmethod
    def get_flag_orders(symbol, binance_features):
        query = "select * from test_trades where trade_flag = 1 and trade_symbol = '%s'" % symbol
        binace_cursor = binance_features.cursor()
        binace_cursor.execute(query)
        data = binace_cursor.fetchone()
        return data

    @staticmethod
    def close_order_finally(trade_id, profitnusd_db, closedprice, current_time, binance_features):
        query = "update test_trades set trade_closedprice = '%s', trade_closedat= '%s',trade_profit = '%s', trade_closereasons='CLOSEDBYPROVIDER', trade_flag = 0 where trade_flag = 1 and trade_id = '%s'" % (closedprice, current_time, profitnusd_db, trade_id)
        binace_cursor = binance_features.cursor()
        binace_cursor.execute(query)
        binace_cursor.close()
        binance_features.commit()