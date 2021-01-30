from datetime import datetime
from typing import List, Tuple, Dict

import numpy as np
import pyqtgraph as pg
import talib
import copy

from vnpy.trader.ui import create_qapp, QtCore, QtGui, QtWidgets
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

from vnpy.chart import ChartWidget, VolumeItem, CandleItem
from vnpy.chart.item import ChartItem
from vnpy.chart.manager import BarManager
from vnpy.chart.base import NORMAL_FONT

from vnpy.trader.engine import MainEngine
from vnpy.event import Event, EventEngine

from vnpy.trader.event import (
    EVENT_TICK,
    EVENT_TRADE,
    EVENT_ORDER,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_LOG
)

from vnpy.trader.object import (
    Direction, 
    Exchange, 
    Interval, 
    Offset, 
    Status, 
    Product, 
    OptionType, 
    OrderType,
    OrderData,
    TradeData,
)

from .item import LineItem, RsiItem, SmaItem, MacdItem, TradeItem, OrderItem

class NewChartWidget(ChartWidget):
    """ 
    基于ChartWidget的K线图表 
    """

    EVENT_CTA_TICK = "eCtaTick"                     # hxxjava add
    EVENT_CTA_HISTORY_BAR = "eCtaHistoryBar"        # hxxjava add
    EVENT_CTA_BAR = "eCtaBar"                       # hxxjava add
    EVENT_CTA_ORDER = "eCtaOrder"                   # hxxjava add  
    EVENT_CTA_TRADE = "eCtaTrade"                   # hxxjava add

    MIN_BAR_COUNT = 100

    signal_cta_history_bar:QtCore.pyqtSignal = QtCore.pyqtSignal(Event)
    signal_cta_tick: QtCore.pyqtSignal = QtCore.pyqtSignal(Event)
    signal_cta_bar:QtCore.pyqtSignal = QtCore.pyqtSignal(Event)

    def __init__(self, parent: QtWidgets.QWidget = None,event_engine: EventEngine = None,strategy_name:str=""):
        """ 初始化 """
        super().__init__(parent)
        self.strategy_name = strategy_name
        self.event_engine = event_engine

        # 创建K线主图及多个绘图部件
        self.add_plot("candle", hide_x_axis=True)
        self.add_item(CandleItem, "candle", "candle")
        self.add_item(LineItem, "line", "candle")
        self.add_item(SmaItem, "sma", "candle")
        self.add_item(OrderItem, "order", "candle")
        self.add_item(TradeItem, "trade", "candle")

        # 创建成交量附图及绘图部件
        self.add_plot("volume", maximum_height=150)
        self.add_item(VolumeItem, "volume", "volume")

        # 创建RSI附图及绘图部件
        self.add_plot("rsi", maximum_height=150)
        self.add_item(RsiItem, "rsi", "rsi")

        # 创建MACD附图及绘图部件
        self.add_plot("macd", maximum_height=150)
        self.add_item(MacdItem, "macd", "macd")

        # 创建最新价格线、光标
        self.add_last_price_line()
        self.add_cursor()
        self.setWindowTitle(f"K线图表") #——{symbol}.{exchange.value},{interval},{start}-{end}")

        # 委托单列表
        self.orders:List[str,OrderData] = {}
        # 成交单列表
        self.trades:List[str,TradeData] = {}

        # self.register_event()
        # self.event_engine.start()

    def register_event(self) -> None:
        """"""
        if self.event_engine == None:
            return
        self.signal_cta_history_bar.connect(self.process_cta_history_bar)
        self.event_engine.register(self.EVENT_CTA_HISTORY_BAR, self.signal_cta_history_bar.emit)

        self.signal_cta_tick.connect(self.process_tick_event)
        self.event_engine.register(self.EVENT_CTA_TICK, self.signal_cta_tick.emit)

        self.signal_cta_bar.connect(self.process_cta_bar)
        self.event_engine.register(self.EVENT_CTA_BAR, self.signal_cta_bar.emit)

    def process_cta_history_bar(self, event:Event) -> None:
        """ 处理历史K线推送 """
        strategy_name,history_bars = event.data
        if strategy_name == self.strategy_name:
            self.update_history(history_bars)

            # print(f" {strategy_name} got an EVENT_CTA_HISTORY_BAR")

    def process_tick_event(self, event: Event) -> None:
        """ 处理tick数据推送 """
        strategy_name,tick = event.data
        if strategy_name == self.strategy_name:
            if self.last_price_line:
                self.last_price_line.setValue(tick.last_price)
            #print(f" {strategy_name} got an EVENT_CTA_TICK")

    def process_cta_bar(self, event:Event)-> None:
        """ 处理K线数据推送 """

        strategy_name,bar = event.data
        if strategy_name == self.strategy_name:
            self.update_bar(bar)
            # print(f"{strategy_name} got an EVENT_CTA_BAR")

    def add_last_price_line(self):
        """"""
        plot = list(self._plots.values())[0]
        color = (255, 255, 255)

        self.last_price_line = pg.InfiniteLine(
            angle=0,
            movable=False,
            label="{value:.1f}",
            pen=pg.mkPen(color, width=1),
            labelOpts={
                "color": color,
                "position": 1,
                "anchors": [(1, 1), (1, 1)]
            }
        )
        self.last_price_line.label.setFont(NORMAL_FONT)
        plot.addItem(self.last_price_line)

    def update_history(self, history: List[BarData]) -> None:
        """
        Update a list of bar data.
        """
        self._manager.update_history(history)

        for item in self._items.values():
            item.update_history(history)

        self._update_plot_limits()

        self.move_to_right()

        self.update_last_price_line(history[-1])

    def update_bar(self, bar: BarData) -> None:
        """
        Update single bar data.
        """
        self._manager.update_bar(bar)

        for item in self._items.values():
            item.update_bar(bar)

        self._update_plot_limits()

        if self._right_ix >= (self._manager.get_count() - self._bar_count / 2):
            self.move_to_right()

        self.update_last_price_line(bar)

    def update_last_price_line(self, bar: BarData) -> None:
        """"""
        if self.last_price_line:
            self.last_price_line.setValue(bar.close_price)

    def add_orders(self,orders:List[OrderData]) -> None:
        """ 
        增加委托单列表到委托单绘图部件 
        """
        for order in orders:
            self.orders[order.orderid] = order

        order_item : OrderItem = self.get_item('order')
        if order_item:
            order_item.add_orders(self.orders.values())

    def add_trades(self,trades:List[TradeData]) -> None:
        """ 
        增加成交单列表到委托单绘图部件 
        """
        for trade in trades:
            self.trades[trade.tradeid] = trade

        trade_item : TradeItem = self.get_item('trade')
        if trade_item:
            trade_item.add_trades(self.trades.values())


