# Signal v2 方法

更新：2026-08-29

## 对产品的解释

首页展示五张卡：Trend、Participation、ROC35 Style、Cycle、Risk；另给一个 Market Regime。
ROC35 保持 `1.0.0` 原公式和字段不变。其余四项是新的连续评分，不再由一两个布尔条件直接下
结论。分数、置信度和每个分项贡献都随 Market Release 公开。

这些评分目前属于 `Observation v2`，不是已证明能产生超额收益的交易策略。产品可以说明当前
环境和确认/失效条件，不得在完成样本外验证前宣称胜率、年化收益或回撤改善。

## 四项评分

### Trend Score（0–100，越高越强）

- SPY、QQQ 短趋势结构（MA20/MA50）：各 15%；
- SPY、QQQ 长趋势结构（MA50/MA200）：各 20%；
- SPY、QQQ 1 月收益相对 20 日年化波动率：各 15%。

`≥65 BULLISH`，`≤35 BEARISH`，其余 `NEUTRAL`。至少 50% 权重可用才出状态。

### Participation Score（0–100，越高越广）

- S&P 500、Nasdaq-100 位于 MA50/MA200 上方的成员比例：合计 60%；
- RSP/SPY、QQEW/QQQ 的 1 月相对收益：合计 20%；
- 两组等权/市值比率是否高于 MA50：合计 20%。

`≥60 BROAD`，`≤40 NARROW`，其余 `MIXED`。广度使用当前成分股，明确存在 survivorship bias。

### Cycle Score（0–100，越高越偏进攻）

- SMH 相对 QQQ 的 1 周与 1 月表现：40%；
- IWM 相对 SPY 的 1 月表现：20%；
- XLY/XLI/XLF 相对 XLP/XLU/XLV 的强弱差：25%；
- 11 行业 ETF 月度正收益扩散率：15%。

`≥60 LEADING`，`≤40 LAGGING`，其余 `MIXED`。

### Risk Score（0–100，越高风险越大）

- VIX 水位 25%，VIX 日变化 10%；
- SPY 20 日/60 日实现波动率加速 20%，当前回撤 15%；
- 10Y 三日利率冲击 10%，OFR 金融压力 10%；
- Participation 的反向压力 10%。

`≤55 OPEN`，`55–75 CAUTION`，`≥75 CLOSED`。VIX 只发布当前值、前值和衍生状态，不公开完整
Cboe 历史。

## 综合状态

Market Regime 使用 `Trend 35% + Participation 30% + Cycle 20% + (100-Risk) 15%`。ROC35 不进入
综合风险分数，因为价值领先与市场看多/看空不是同一件事；它仍完整显示在风格卡中。

- 分数 ≥65 且 Risk <55：`RISK_ON`；
- 分数 <35 或 Risk ≥75：`DEFENSIVE`；
- 其余：`WATCH`；
- 综合置信度 <65%：`UNAVAILABLE`。

多周期趋势和风险缩放的研究背景可参考 [Time Series Momentum](https://doi.org/10.1016/j.jfineco.2011.11.003)
与 [Volatility-Managed Portfolios](https://doi.org/10.1111/jofi.12513)。这里的实现是 ArcOfMarket
自己的透明规则，不声称复制论文策略。
