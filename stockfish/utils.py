import math
from datamodel import Order


class Util:
    @staticmethod
    def get_best_bid(order_depth):
        """
        Returns the best bid and its volume
        """
        if len(order_depth.buy_orders) == 0:
            return None, None
        best_bid = max(order_depth.buy_orders.keys())
        best_bid_volume = order_depth.buy_orders[best_bid]
        return best_bid, best_bid_volume


    @staticmethod
    def get_best_ask(order_depth):
        """
        Returns the best ask and its volume
        """
        if len(order_depth.sell_orders) == 0:
            return None, None
        best_ask = min(order_depth.sell_orders.keys())
        best_ask_volume = -order_depth.sell_orders[best_ask]
        return best_ask, best_ask_volume


    @staticmethod
    def get_mid_price(order_depth):
        """
        Returns the mid price
        """
        best_bid, _ = Util.get_best_bid(order_depth)
        best_ask, _ = Util.get_best_ask(order_depth)
        if best_bid is None or best_ask is None:
            return None
        return (best_bid + best_ask) / 2


    @staticmethod
    def get_moving_average(trades, window_size):
        """
        Returns the moving average of the last window_size trades
        """
        window_size = min(len(trades), window_size)
        return sum(trade.price for trade in trades[-window_size:]) / window_size


    @staticmethod
    def get_moving_std(trades, window_size):
        """
        Returns the moving standard deviation of the last window_size trades
        """
        window_size = min(len(trades), window_size)
        mean = Util.get_moving_average(trades, window_size)
        return math.sqrt(sum((trade.price - mean) ** 2 for trade in trades[-window_size:]) / window_size)


    @staticmethod
    def get_vwap(orders):
        """
        orders = order_depth.buy_orders or order_depth.sell_orders
        """
        weighted_sum = 0
        quantity_sum = 0
        for price in orders:
            quantity = orders[price]
            weighted_sum += price * quantity
            quantity_sum += quantity
        return weighted_sum / quantity_sum if quantity_sum != 0 else 0


    @staticmethod
    def place_buy_order(product, orders, price, quantity):
        """
        Places a buy order
        """
        quantity = abs(quantity)
        print("BUY", str(quantity) + "x", price)
        orders.append(Order(product, price, quantity))


    @staticmethod
    def place_sell_order(product, orders, price, quantity):
        """
        Places a sell order
        """
        quantity = abs(quantity)
        print("SELL", str(quantity) + "x", price)
        orders.append(Order(product, price, -quantity))
