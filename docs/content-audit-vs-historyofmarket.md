# ArcOfMarket vs HistoryOfMarket — 内容对齐审计

## 标普 500

| HoM 章节 | HoM 内容 | 我们有没有 | 差距 |
|----------|---------|-----------|------|
| **§ I · The Shape of a Century** | | | |
| Annual Returns | 年度涨跌柱状图，1928→ | ✅ sp500-annual | 文案需加强：HoM 说"73 涨 26 跌，平均 11.8%，但贴着均值的年份只有 7 个" |
| Return Distribution | 回报分布直方图 | ✅ sp500-distribution | HoM 强调"算术平均的误导性"——这个角度我们没讲 |
| Buy/Sell Matrix | 任选买卖年份矩阵 | ✅ sp500-rollmatrix | HoM 叫"Pick Any Entry Year, Any Exit Year"，更接地气 |
| Rolling 5Y CAGR | 五年滚动年化 | ✅ sp500-rolling5y | HoM 说"负回报窗口不足一成"——简洁有力 |
| Total Return Decomposition | 回报 = 价格 + 股息 + 回购 | ❌ | **没有！** 1999→ 的回报拆解，回购正在超过股息 |
| Log YoY Bull/Bear | 对数同比牛熊 | ✅ sp500-bullbear | HoM 叫"十四次穿越零线"，更形象 |
| **§ II · Distribution & Extremes** | | | |
| Daily Distribution | 日涨跌分布 + 正态曲线叠加 | ❌ | **没有！** 展示"肥尾"——极端日远超正态分布预测 |
| Extreme Days Multiplier | 极端日的复利效应 | ❌ (部分覆盖) | HoM 算"错过最好的 N 天 vs 躲过最坏的 N 天"的复利差异 |
| **§ III · Anchors of Valuation** | | | |
| Shiller CAPE | 周期平滑 PE | ❌ | **没有！** 需要 Shiller 数据，这是估值锚点的核心 |
| AIAE (Investor Allocation) | 美国股市配置占比 | ✅ equity_allocation | HoM 声称"比 CAPE 更准地预测十年回报" |
| TTM PE × Forward PE | 双 PE 对标 | ❌ | **没有！** Forward PE 需要 Bloomberg 数据 |
| Return Decomposition (TTM) | 每年 = 估值变化 × 盈利变化 | ❌ | **没有！** 拆解"今年涨是因为盈利涨还是估值涨" |
| EPS (TTM) | 每股收益序列 1871→ | ❌ | 需要 Shiller 数据 |
| ROE | 净资产收益率 | ❌ | ROE 近二十年稳定在 15%——很好的"长期锚" |
| **§ IV · The Rhythm of Crisis** | | | |
| Major Drawdowns | 每次大跌有名字和故事 | ✅ sp500-drawdowns | HoM 标注分类、诱因、恢复天数 |
| Intrayear Drawdown | 年内回撤 vs 全年结果 | ✅ sp500-intrayear | HoM 说"跌了就跑是最贵的策略" |
| Realized Volatility | 20/60 日滚动波动 | ✅ sp500-volatility | HoM 叫"市场的呼吸频率" |
| VIX | 隐含波动率 | ✅ sp500-vol-family | HoM 叫"保险费的账本" |
| Bull-Market Breadth | 多少成分在均线之上 | ❌ | **没有！** 窄幅上涨 vs 普涨的区别 |
| Monthly Seasonality | 月份热力图 | ✅ sp500-seasonality | HoM 用热力图表现，比柱状图直观 |
| Gold in Drawdowns | 黄金在美股下跌时表现 | ❌ | 需要 UBS Yearbook 数据 |
| **§ V · Anatomy** | | | |
| Sector Turnover | 1900 vs 今天行业权重对比 | ❌ | **震撼！** 铁路从 63% 到 <1% |
| Index Rules | S&P 500 编制规则 | ❌ | 教育性内容 |
| Sector Weights | GICS 11 行业权重 | ✅ Sp500Composition | |
| Mag7 Equal-Weight | 七巨头等权 | ✅ (在 /mag7 页面) | |
| Constituent Changes | 调入调出 | ✅ | |

**标普 500 总结：我们有 13/23，缺 10 个。最关键的缺失：CAPE/PE 估值系列、日分布、回报拆解。**

---

## 纳斯达克

| HoM 章节 | HoM 内容 | 我们有没有 | 差距 |
|----------|---------|-----------|------|
| **§ I · Composite** | | | |
| Composite Century | 综指 50 年 | ✅ ixic-century | |
| Log YoY Bull/Bear | 对数同比 | ✅ ixic-bullbear | |
| Constituent Ranking | 1W/1M/YTD/1Y 排名 | ❌ | **没有！** 纳指 100 全部成分的涨跌排名 |
| All-member Scatter | 市值 × 一年回报 | ❌ | TradingView heatmap 部分替代 |
| **§ II · Distribution** | | | |
| Daily Distribution | 日分布 vs 正态 | ❌ | 纳指的肥尾比标普更极端 |
| Extreme Days | 极端日复利 | ❌ | |
| **§ III · Valuation** | | | |
| Forward PE | NDX 远期 PE | ❌ | **没有！** 2001→ 的月度远期 PE，dotcom 峰值 190+ 倍 |
| Return Decomposition | 重定价 × 盈利修正 | ❌ | |
| **§ IV · Returns** | | | |
| QQQ Annual Returns | 年度回报 | ✅ ndx-annual | |
| Return Distribution | 回报分布 | ✅ ndx-distribution | |
| Buy/Sell Matrix | 买卖矩阵 | ✅ ndx-rollmatrix | |
| Rolling 5Y | 五年滚动 | ✅ ndx-rolling5y | |
| QQQ Return Decomposition | 价格/股息/回购 | ❌ | |
| **§ V · Crisis** | | | |
| Major Drawdowns | 59 次回撤 | ✅ ndx-drawdowns | 2000-2002 累计 -83%，这个数字要强调 |
| Intrayear Drawdown | 年内回撤 | ✅ ndx-intrayear | |
| Realized Volatility | 实现波动 | ✅ ndx-volatility | 纳指中位数 ~22%，系统性高于标普 |
| VXN | 纳指波动率指数 | ❌ | **没有！** 纳指自己的 VIX |
| Breadth | 均线之上占比 | ❌ | |
| Monthly Heatmap | 月度热力图 | ❌ (有柱状图) | HoM 用热力图更直观 |
| **§ VI · Anatomy** | | | |
| Top Holdings | 前 25 大持仓 | ✅ ndx-cross-section | |
| Constituents | 全部成分 | ❌ | |
| Changes | 调入调出 | ❌ | |

**纳斯达克总结：我们有 14/25，缺 11 个。最关键的缺失：Forward PE、VXN、成分排名、日分布。**

---

## 道琼斯

| HoM 内容 | 我们有没有 | 差距 |
|----------|-----------|------|
| DJI 百年价格 | ✅ dji-century | |
| 年度回报 | ✅ dji-annual | |
| 回撤 | ✅ dji-drawdowns | |
| DIA/SPY/QQQ 对比 | ✅ dow-etf-proxies | |

**道琼斯：HoM 的道琼斯内容相对较少（在该站不是重点），我们基本对齐。**

---

## 七巨头

| HoM 章节 | HoM 内容 | 我们有没有 | 差距 |
|----------|---------|-----------|------|
| **§ I** | | | |
| Equal-Weight Index | 等权指数 vs SP500 | ✅ mag7-equal-weight | |
| **§ II** | | | |
| Share of S&P 500 | 七家占标普权重 | ❌ | **非常震撼的数据！** 13%→33%+ |
| Hyperscaler CapEx | AI 资本开支 vs 回购 | ❌ | "四家在烧钱，三家在还钱" |
| **§ III** | | | |
| Per-member Drawdown | 每家回撤路径 | ✅ mag7-drawdowns | META 2022 -77%，这个数字一定要讲 |
| **§ IV** | | | |
| 60-Day Correlation | 七家相关矩阵 | ❌ | "七只是不是变成了一只？" |
| AI Valuation vs 1999 | NVDA vs CSCO/ORCL/SUNW | ✅ mag7-valuation | |
| **§ V** | | | |
| Historical Lineage | Nifty50→四骑士→FANG→Mag7 | ❌ | **极好的叙事！** 科技龙头的代际更替 |

**七巨头总结：我们有 3/7，缺 4 个。最关键的缺失：权重占比、相关性、历史谱系、AI 资本开支。**

---

## 宏观

| 内容 | 我们有没有 |
|------|-----------|
| 利率 (SOFR/EFFR/Yields/Spreads) | ✅ MacroDashboard |
| 物价 (CPI/PCE/PPI) | ✅ macro-prices |
| 增长 (GDP/Employment) | ✅ macro-growth |
| 金融压力 (OFR FSI) | ✅ FinancialStress |
| VIX 仓位 (CFTC COT) | ✅ cot_vix |
| 信用利差 | ✅ macro-credit |
| 股票配置占比 | ✅ equity-allocation |
| 衰退期 | ✅ recessions |

**宏观总结：HoM 的宏观内容分散在多个页面，我们没有独立的全面宏观页但各组件齐全。**

---

## 我们独有的（HoM 没有的）

| 内容 | 说明 |
|------|------|
| 首页"今日判断" | 每日市场温度——对标 MarketGrep，这是我们的差异化 |
| 策略信号 (4 lenses) | ARC TREND/PULSE/BALANCE/CLOCK——商业化入口 |
| 五幕市场故事 | 首页叙事长卷 |
| 行业板块主题页 | 12 个 GICS 行业深度页 |
| Regime Rotation | 六状态量化策略 |
| RS Leaders | 相对强弱指数 |

---

## 结论：我们应该优先做什么

### P0 — 补齐最震撼的数据（能讲好故事）

1. **七巨头权重占比** — "七家占了标普三分之一"这个数字太震撼，必须展示
2. **标普 500 CAPE/PE 估值** — 这是"现在贵不贵"的标准答案
3. **纳斯达克 VXN** — 纳指自己的恐慌指数

### P1 — 增强叙事深度

4. **日涨跌分布** — 标普和纳指都加，"肥尾"是最重要的统计课
5. **标普 500 回报拆解**（价格+股息+回购）— 教育用户"总回报"的真正含义
6. **七巨头相关性** — "七只是一只？"好问题
7. **七巨头谱系** — Nifty50→FANG→Mag7，科技龙头代际更替的故事

### P2 — 精装修

8. **行业更替历史** — 铁路→科技，像 HoM 那样震撼
9. **月度热力图** — 比柱状图直观
10. **纳指成分排名** — 1W/1M/YTD/1Y
