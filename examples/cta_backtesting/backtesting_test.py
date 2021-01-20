# To add a new cell, type ''
# To add a new markdown cell, type ' [markdown]'

from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.strategies.test_strategy import (
    TestStrategy,
)
from datetime import datetime



engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="rb1910.SHFE",
    interval="1h",
    start=datetime(2019, 9, 1),
    end=datetime(2019, 9, 30),
    rate=0.3/10000,
    slippage=0.2,
    size=10,
    pricetick=0.2,
    capital=1_000_000,
)
engine.add_strategy(TestStrategy, {})



engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()
# engine.show_chart()



# setting = OptimizationSetting()
# setting.set_target("sharpe_ratio")
# setting.add_parameter("atr_length", 3, 39, 1)
# setting.add_parameter("atr_ma_length", 10, 30, 1)

# engine.run_ga_optimization(setting)


