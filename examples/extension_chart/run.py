from datetime import datetime

from vnpy.trader.ui import create_qapp, QtCore
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Exchange, Interval
from vnpy.chart import ChartWidget, VolumeItem, CandleItem
from vnpy.extension.chart import NewChartWidget

if __name__ == "__main__":
    app = create_qapp()

    bars = database_manager.load_bar_data(
        "sc2103",
        Exchange.INE,
        interval=Interval.MINUTE,
        start=datetime(2021, 1, 1),
        end=datetime(2021, 1, 31)
    )

    print(f"一共读取{len(bars)}根K线")

    event_engine = None
    # event_engine = EventEngine()

    widget = NewChartWidget(event_engine = event_engine)

    dynamic = False  # 是否动态演示
    n = 1000          # 缓冲K线根数
    if dynamic:
        history = bars[:n]      # 先取得最早的n根bar作为历史
        new_data = bars[n:]     # 其它留着演示
    else:
        history = bars          # 先取得最新的n根bar作为历史
        new_data = []           # 演示的为空

    # 绘制历史K线主图及各个副图
    widget.update_history(history)

    # # 绘制委托单到主图
    # orders = make_orders()
    # widget.add_orders(orders)

    # # 绘制成交单到主图
    # trades = make_trades()
    # widget.add_trades(trades)

    def update_bar():
        if new_data:
            bar = new_data.pop(0)
            widget.update_bar(bar)

    timer = QtCore.QTimer()
    timer.timeout.connect(update_bar)
    if dynamic:
        timer.start(100)

    widget.show()

    # event_engine.start()
    app.exec_()