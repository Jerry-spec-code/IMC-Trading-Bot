import math
import json
from typing import Dict, List, Any
from datamodel import OrderDepth, TradingState, Order, ProsperityEncoder, Symbol

class Trader:
    """
    Trading a stable and trending market respectively by comparing two different moving averages.
    Monitor changes in the bid/ask prices and place limit orders accordingly.
    """
    def __init__(self):
        self.position_limit = {"PEARLS": 20, "BANANAS": 20}
        self.ask_price = {}
        self.bid_price = {}
        self.vwap_bid_prices = {}
        self.vwap_ask_prices = {}

        # moving average data
        self.large_ask_averages = {}
        self.small_ask_averages = {}
        self.large_bid_averages = {}
        self.small_bid_averages = {}
        self.window_size_small = 100
        self.window_size_large = 500

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """"
        Main entry point for the algorithm
        """
        result = {}

        for product, order_depth in state.order_depths.items():
            orders: list[Order] = []
            position = state.position.get(product, 0)
            position_limit = self.position_limit.get(product, 0)
            buy_volume = position_limit - position
            sell_volume = position_limit + position
            best_ask, best_ask_volume = get_best_ask(order_depth)
            best_bid, best_bid_volume = get_best_bid(order_depth)
            best_ask_volume = min(-best_ask_volume, buy_volume)
            best_bid_volume = min(best_bid_volume, sell_volume)
            self.ask_price[product] = min(self.ask_price.get(product, best_ask), best_ask)
            self.bid_price[product] = max(self.bid_price.get(product, best_bid), best_bid)

            if product == "PEARLS":
                if self.ask_price[product] < self.bid_price[product]:
                    place_buy_order(product, orders, self.ask_price[product], buy_volume)
                    place_sell_order(product, orders, self.bid_price[product], sell_volume)
            elif product == "BANANAS":

                self.order_by_vwap(
                    product=product,
                    prices=self.vwap_bid_prices,
                    large_averages=self.large_bid_averages,
                    small_averages=self.small_bid_averages,
                    book=order_depth.buy_orders,
                    order_condition=lambda : self.sell_signal(product),
                    place_order_function=lambda : place_sell_order(product, orders, best_bid, best_bid_volume)
                )

                self.order_by_vwap(
                    product=product,
                    prices=self.vwap_ask_prices,
                    large_averages=self.large_ask_averages,
                    small_averages=self.small_ask_averages,
                    book=order_depth.sell_orders,
                    order_condition=lambda : self.buy_signal(product),
                    place_order_function=lambda : place_buy_order(product, orders, best_ask, best_ask_volume)
                )

            result[product] = orders

        logger.flush(state, orders)
        return result

    def sell_signal(self, product):
        large_averages = self.large_bid_averages[product]
        small_averages = self.small_bid_averages[product]
        if len(large_averages) < self.window_size_small:
            return False
        cur_roc_large, cur_roc_small, past_roc_large, past_roc_small = self.get_crossover_data(large_averages, small_averages)
        return cur_roc_large > cur_roc_small and past_roc_large < past_roc_small

    def buy_signal(self, product):
        large_averages = self.large_ask_averages[product]
        small_averages = self.small_ask_averages[product]
        if len(large_averages) < self.window_size_small:
            return False
        cur_roc_large, cur_roc_small, past_roc_large, past_roc_small = self.get_crossover_data(large_averages, small_averages)
        return cur_roc_large < cur_roc_small and past_roc_large > past_roc_small

    def get_crossover_data(self, large_averages, small_averages):
        cur_roc_large = large_averages[-1]
        cur_roc_small = small_averages[-1]
        past_roc_large = large_averages[-2]
        past_roc_small = small_averages[-2]
        return cur_roc_large, cur_roc_small, past_roc_large, past_roc_small  

    def get_roc_data(self, large_averages, small_averages):
        cur_roc_large = self.get_average_roc(large_averages)
        cur_roc_small = self.get_average_roc(small_averages)
        past_roc_large = self.get_average_roc(large_averages[:-1])
        past_roc_small = self.get_average_roc(small_averages[:-1])
        return cur_roc_large, cur_roc_small, past_roc_large, past_roc_small 

    def get_average_roc(self, data):
        roc = []
        for i in range(1, len(data)):
            new_val = data[i]
            old_val = data[i-1]
            rate = (new_val - old_val) / old_val * 100
            roc.append(rate)
        return sum(roc) / len(roc)

    def order_by_vwap(self, product, prices, 
                      large_averages, 
                      small_averages, 
                      book, 
                      order_condition, 
                      place_order_function):
        self.init_list(product, prices)
        self.init_list(product, large_averages)
        self.init_list(product, small_averages)
        prices[product].append(get_vwap(book))
        if self.not_enough_data(product, prices):
            return
        large_averages[product].append(get_moving_average(prices[product], self.window_size_large))
        small_averages[product].append(get_moving_average(prices[product], self.window_size_small))
        if order_condition():
            place_order_function()

    def init_list(self, product, lst):
        if product not in lst:
            lst[product] = []
    
    def not_enough_data(self, product, prices):
        return len(prices[product]) < self.window_size_large

    


class Logger:
    def __init__(self) -> None:
        self.logs = ""

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]]) -> None:
        print(json.dumps({
            "state": state,
            "orders": orders,
            "logs": self.logs,
        }, cls=ProsperityEncoder, separators=(",", ":"), sort_keys=True))

        self.logs = ""

logger = Logger()


def get_best_bid(order_depth):
    """
    Returns the best bid and its volume
    """
    if len(order_depth.buy_orders) == 0:
        return None, None
    best_bid = max(order_depth.buy_orders)
    best_bid_volume = order_depth.buy_orders[best_bid]
    return best_bid, best_bid_volume


def get_best_ask(order_depth):
    """
    Returns the best ask and its volume
    """
    if len(order_depth.sell_orders) == 0:
        return None, None
    best_ask = min(order_depth.sell_orders)
    best_ask_volume = order_depth.sell_orders[best_ask]
    return best_ask, best_ask_volume


def get_spread(order_depth):
    """
    Returns the spread
    """
    best_bid, _ = get_best_bid(order_depth)
    best_ask, _ = get_best_ask(order_depth)
    if best_bid is None or best_ask is None:
        return None
    return best_ask - best_bid


def get_mid_price(order_depth):
    """
    Returns the mid price
    """
    best_bid, _ = get_best_bid(order_depth)
    best_ask, _ = get_best_ask(order_depth)
    if best_bid is None or best_ask is None:
        return None
    return (best_bid + best_ask) / 2


def get_moving_average(prices, window_size):
    """
    Returns the moving average of the last window_size trades
    """
    window_size = min(len(prices), window_size)
    return sum(price for price in prices[-window_size:]) / window_size


def get_moving_std(trades, window_size):
    """
    Returns the moving standard deviation of the last window_size trades
    """
    window_size = min(len(trades), window_size)
    mean = get_moving_average(trades, window_size)
    return math.sqrt(sum((trade.price - mean) ** 2 for trade in trades[-window_size:]) / window_size)


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


def place_buy_order(product, orders, price, quantity):
    """
    Places a buy order
    """
    quantity = abs(quantity)
    print("BUY", str(quantity) + "x", price)
    orders.append(Order(product, price, quantity))


def place_buy_orders_up_to(product, orders, quantity, order_depth):
    """
    Places buy orders up to a given quantity
    """
    quantity = abs(quantity)
    start = min(order_depth.sell_orders.keys())
    finish = max(order_depth.sell_orders.keys())
    for price in range(start, finish + 1):
        if price in order_depth.sell_orders:
            best_ask_volume = abs(order_depth.sell_orders[price])
            quantity = min(quantity, best_ask_volume)
            place_buy_order(product, orders, price, quantity)
            quantity -= best_ask_volume
            if quantity <= 0:
                return
    
    # for best_ask, best_ask_volume in dict(sorted(order_depth.sell_orders.items())):
    #     best_ask_volume = abs(best_ask_volume)
    #     quantity = min(quantity, best_ask_volume)
    #     print("BUY", str(quantity) + "x", best_ask)
    #     orders.append(Order(product, best_ask, quantity))
    #     quantity -= best_ask_volume
    #     if quantity <= 0:
    #         return


def place_sell_order(product, orders, price, quantity):
    """
    Places a sell order
    """
    quantity = abs(quantity)
    print("SELL", str(quantity) + "x", price)
    orders.append(Order(product, price, -quantity))


def place_sell_orders_up_to(product, orders, quantity, order_depth):
    """
    Places sell orders up to a given quantity
    """
    quantity = abs(quantity)
    start = max(order_depth.buy_orders.keys())
    finish = min(order_depth.buy_orders.keys())
    for price in range(start, finish - 1, -1):
        if price in order_depth.buy_orders:
            best_bid_volume = abs(order_depth.buy_orders[price])
            quantity = min(quantity, best_bid_volume)
            place_sell_order(product, orders, price, quantity)
            quantity -= best_bid_volume
            if quantity <= 0:
                return

    # quantity = abs(quantity)
    # for best_bid, best_bid_volume in dict(sorted(order_depth.buy_orders.items(), reverse=True)):
    #     best_bid_volume = abs(best_bid_volume)
    #     quantity = min(quantity, best_bid_volume)
    #     print("SELL", str(quantity) + "x", best_bid)
    #     orders.append(Order(product, best_bid, -quantity))
    #     quantity -= best_bid_volume
    #     if quantity <= 0:
    #         return
