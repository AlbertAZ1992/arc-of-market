import type { ChartIndex } from "@/content/types";

/**
 * 图表索引 — 所有可渲染的图表定义。
 *
 * 每个 key 对应一个图表，定义了数据路径、渲染类型、数据来源。
 * 页面 schema 通过 key 引用图表，不直接写 dataPath 和 kind。
 *
 * 要新增图表：在这里加一个 entry，然后在页面 schema 的 blocks 中引用。
 * 要修改图表配置：只改这里，所有引用该图表的页面自动更新。
 */
export const chartIndex = {
  // ─── S&P 500 ───
  "sp500-century": {
    title: "S&P 500 长期价格指数",
    dataPath: "/data/sp500_century.json",
    kind: "price",
    scaleType: "log",
    yUnit: "指数点位",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-total-return": {
    title: "S&P 500 总回报指数",
    dataPath: "/data/sp500_total_return.json",
    description:
      "总回报指数把现金股息按指数口径重新投入，价格指数不包含这部分回报。",
    interpretation: ["与价格指数的长期结果相比，差异来自现金股息及其再投资。"],
    kind: "valuation",
    scaleType: "log",
    yUnit: "指数点位",
    valueKey: "values",
    valueLabel: "总回报指数",
    source: "Yahoo Finance · S&P 500 Total Return Index",
    whatToWatch: ["比较累计差距，不把单年股息率直接外推为长期回报。"],
  },
  "sp500-annual": {
    title: "S&P 500 每年的回报落在哪里？",
    dataPath: "/data/sp500_annual.json",
    kind: "annual",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-bullbear": {
    title: "牛市持续多久，熊市回撤多深？",
    dataPath: "/data/sp500_bullbear.json",
    kind: "cycles",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-extremes": {
    title: "S&P 500 最大单日上涨与下跌",
    dataPath: "/data/sp500_extremes.json",
    kind: "extremes",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-distribution": {
    title: "S&P 500 年度回报分布",
    dataPath: "/data/sp500_distribution.json",
    kind: "distribution",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-holding": {
    title: "持有期拉长后，历史亏损概率怎样变化？",
    dataPath: "/data/sp500_holding.json",
    kind: "holding",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-rollmatrix": {
    title: "不同起点怎样改变五年、十年和二十年结果？",
    dataPath: "/data/sp500_rollmatrix.json",
    kind: "rollmatrix",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-rolling5y": {
    title: "任意起点持有五年的年化回报",
    dataPath: "/data/sp500_rolling5y.json",
    kind: "rolling",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-intrayear": {
    title: "年内最大回撤和全年回报是什么关系？",
    dataPath: "/data/sp500_intrayear.json",
    kind: "intrayear",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-seasonality": {
    title: "各月份的平均回报与上涨概率",
    dataPath: "/data/sp500_seasonality.json",
    kind: "seasonality",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-drawdowns": {
    title: "主要历史回撤的跌幅与修复时间",
    dataPath: "/data/sp500_drawdowns.json",
    kind: "drawdown",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-volatility": {
    title: "实现波动率在危机前后怎样变化？",
    dataPath: "/data/sp500_volatility.json",
    kind: "volatility",
    source: "Yahoo Finance 历史价格 · Cboe · ArcOfMarket 计算",
  },
  "sp500-vol-family": {
    title: "VIX 9 日至 1 年期限结构与 SKEW",
    dataPath: "/data/vol_family.json",
    kind: "nested",
    source: "Cboe 历史数据",
    series: [
      { key: "VIX9D", label: "VIX9D", unit: "指数", valueKey: "close" },
      { key: "VIX", label: "VIX", unit: "指数", valueKey: "close" },
      { key: "VIX3M", label: "VIX3M", unit: "指数", valueKey: "close" },
      { key: "VIX6M", label: "VIX6M", unit: "指数", valueKey: "close" },
      { key: "VIX1Y", label: "VIX1Y", unit: "指数", valueKey: "close" },
      { axis: 1, key: "SKEW", label: "SKEW", unit: "指数", valueKey: "close" },
    ],
  },
  "sp500-cross-section": {
    title: "今天是谁在推动 S&P 500？",
    dataPath: "", // TradingView heatmap, no data file
    kind: "price",
    source: "TradingView SPX500",
  },
  "sp500-changes": {
    title: "哪些公司被调入，哪些公司被剔除？",
    dataPath: "/data/sp500_changes.json",
    kind: "changes",
    source: "Wikipedia 固定版本 · CC BY-SA 4.0",
  },
  "sp500-return-decomp": {
    title: "每年的回报，多少来自股价，多少来自股息？",
    dataPath: "/data/sp500_return_decomp.json",
    description: "价格回报与总回报之间的差额，就是股息及再投资贡献。",
    interpretation: [
      "单年差距通常不大，长时间复利后会形成明显的累计回报差距。",
    ],
    kind: "drivers",
    source: "Yahoo Finance · ArcOfMarket 计算",
    whatToWatch: ["比较长期累计结果，不用某一年的股息差额预测下一年回报。"],
  },
  "sp500-breadth": {
    title: "指数上涨时，有多少成分股真正参与？",
    dataPath: "/data/sp500_breadth.json",
    description: "统计当前成分股中高于 50 日和 200 日移动均线的比例。",
    interpretation: ["50 日广度反映短期参与度，200 日广度反映中期趋势覆盖面。"],
    kind: "multiline",
    note: "历史序列使用当前成分股，存在幸存者偏差。",
    series: [
      { key: "pct_above_50ma", label: ">50MA", unit: "%" },
      { key: "pct_above_200ma", label: ">200MA", unit: "%" },
    ],
    source: "Yahoo Finance · ArcOfMarket 计算",
    whatToWatch: ["指数创新高而广度持续下降，说明上涨越来越依赖少数大权重。"],
  },

  // ─── Nasdaq Composite ───
  "ixic-century": {
    title: "Nasdaq Composite 的长期价格路径",
    dataPath: "/data/ixic_century.json",
    kind: "price",
    scaleType: "log",
    yUnit: "指数点位",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-annual": {
    title: "Nasdaq Composite 每年的回报落在哪里？",
    dataPath: "/data/ixic_annual.json",
    kind: "annual",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-bullbear": {
    title: "Nasdaq Composite 的牛熊幅度与持续时间",
    dataPath: "/data/ixic_bullbear.json",
    kind: "cycles",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-extremes": {
    title: "Nasdaq Composite 的极端单日回报",
    dataPath: "/data/ixic_extremes.json",
    kind: "extremes",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-distribution": {
    title: "Nasdaq Composite 的年度回报分布",
    dataPath: "/data/ixic_distribution.json",
    kind: "distribution",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-holding": {
    title: "持有期拉长后，纳斯达克亏损概率怎样变化？",
    dataPath: "/data/ixic_holding.json",
    kind: "holding",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-rollmatrix": {
    title: "不同起点怎样改变纳斯达克长期结果？",
    dataPath: "/data/ixic_rollmatrix.json",
    kind: "rollmatrix",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-rolling5y": {
    title: "Nasdaq Composite 滚动五年年化回报",
    dataPath: "/data/ixic_rolling5y.json",
    kind: "rolling",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-intrayear": {
    title: "纳斯达克年内最大回撤与全年结果",
    dataPath: "/data/ixic_intrayear.json",
    kind: "intrayear",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-seasonality": {
    title: "Nasdaq Composite 各月份的历史表现",
    dataPath: "/data/ixic_seasonality.json",
    kind: "seasonality",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-drawdowns": {
    title: "Nasdaq Composite 的主要历史回撤",
    dataPath: "/data/ixic_drawdowns.json",
    kind: "drawdown",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-volatility": {
    title: "Nasdaq Composite 的实现波动率",
    dataPath: "/data/ixic_volatility.json",
    kind: "volatility",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },

  // ─── Nasdaq-100 ───
  "ndx-century": {
    title: "Nasdaq-100 的长期价格路径",
    dataPath: "/data/ndx_century.json",
    kind: "price",
    scaleType: "log",
    yUnit: "指数点位",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-annual": {
    title: "Nasdaq-100 年度回报",
    dataPath: "/data/ndx_annual.json",
    kind: "annual",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-bullbear": {
    title: "Nasdaq-100 的牛熊幅度与持续时间",
    dataPath: "/data/ndx_bullbear.json",
    kind: "cycles",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-extremes": {
    title: "Nasdaq-100 的极端单日回报",
    dataPath: "/data/ndx_extremes.json",
    kind: "extremes",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-distribution": {
    title: "Nasdaq-100 年度回报分布",
    dataPath: "/data/ndx_distribution.json",
    kind: "distribution",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-holding": {
    title: "持有期拉长后，Nasdaq-100 亏损概率怎样变化？",
    dataPath: "/data/ndx_holding.json",
    kind: "holding",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-rollmatrix": {
    title: "不同起点怎样改变 Nasdaq-100 长期结果？",
    dataPath: "/data/ndx_rollmatrix.json",
    kind: "rollmatrix",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-rolling5y": {
    title: "Nasdaq-100 滚动五年年化回报",
    dataPath: "/data/ndx_rolling5y.json",
    kind: "rolling",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-intrayear": {
    title: "Nasdaq-100 年内最大回撤与全年结果",
    dataPath: "/data/ndx_intrayear.json",
    kind: "intrayear",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-seasonality": {
    title: "Nasdaq-100 各月份的历史表现",
    dataPath: "/data/ndx_seasonality.json",
    kind: "seasonality",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-drawdowns": {
    title: "Nasdaq-100 主要历史回撤",
    dataPath: "/data/ndx_drawdowns.json",
    kind: "drawdown",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-volatility": {
    title: "Nasdaq-100 的实现波动率",
    dataPath: "/data/ndx_volatility.json",
    kind: "volatility",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-cross-section": {
    title: "Nasdaq-100 的上涨集中在哪些公司？",
    dataPath: "",
    kind: "price",
    source: "TradingView NASDAQ100",
  },
  "ndx-valuation-proxy": {
    title: "纳指 100 动态估值代理",
    dataPath: "/data/ndx_valuation_proxy.json",
    description: "每日保存 QQQ trailing PE，用同一口径积累可比较的估值历史。",
    interpretation: [
      "当前序列较短，先用于跟踪方向，不能替代完整周期估值分布。",
    ],
    kind: "multiline",
    source: "Yahoo Finance QQQ 基本面元数据",
    note: "这是 QQQ trailing PE 代理，不是 Nasdaq 官方 NDX PE，也不是 Forward PE。",
    series: [{ key: "trailing_pe", label: "QQQ TTM PE", unit: "倍" }],
    whatToWatch: ["区分价格下降导致的估值回落与盈利上升导致的估值消化。"],
  },
  "ndx-breadth": {
    title: "Nasdaq-100 的上涨扩散到多少家公司？",
    dataPath: "/data/ndx_breadth.json",
    description: "统计当前成分股中高于 50 日和 200 日移动均线的比例。",
    interpretation: ["与指数价格对照，可以区分普遍上涨和少数龙头拉动。"],
    kind: "multiline",
    note: "历史序列使用当前成分股，存在幸存者偏差。",
    series: [
      { key: "pct_above_50ma", label: ">50MA", unit: "%" },
      { key: "pct_above_200ma", label: ">200MA", unit: "%" },
    ],
    source: "Yahoo Finance · ArcOfMarket 计算",
    whatToWatch: ["价格上升但 50 日广度下降，说明集中度风险正在上升。"],
  },

  // ─── Mag7 ───
  "mag7-equal-weight": {
    title: "七巨头等权篮子相对大盘表现如何？",
    dataPath: "/data/mag7_equal_weight.json",
    kind: "price",
    source: "Yahoo Finance · ArcOfMarket 计算",
    eyebrow: "EQUAL-WEIGHT BASKET",
  },
  "mag7-prices": {
    title: "七家公司的回报差距有多大？",
    dataPath: "/data/mag7_prices.json",
    kind: "price",
    source: "Yahoo Finance · ArcOfMarket 计算",
    eyebrow: "NORMALIZED COMPARISON",
  },
  "mag7-valuation": {
    title: "Nvidia 与 Cisco 高增长时期的估值对照",
    dataPath: "/data/nvda_csco_valuation.json",
    kind: "multiline",
    source: "Yahoo Finance 基本面元数据 · ArcOfMarket 积累",
    eyebrow: "VALUATION ANCHOR",
  },

  // ─── Dow ───
  "dow-etf-proxies": {
    title: "DIA、SPY、QQQ 的长期相对表现",
    dataPath: "/data/etf_proxies.json",
    description:
      "三只 ETF 在最早共同日期归一化为 100，比较蓝筹、大盘和成长风格。",
    interpretation: ["曲线差距表示长期相对表现，不代表下一阶段必然均值回归。"],
    kind: "nested",
    source: "Yahoo Finance · ArcOfMarket 计算",
    eyebrow: "BENCHMARK COMPARISON",
    series: [
      { key: "DIA", label: "Dow", unit: "归一化指数" },
      { key: "SPY", label: "S&P 500", unit: "归一化指数" },
      { key: "QQQ", label: "Nasdaq-100", unit: "归一化指数" },
    ],
    whatToWatch: ["观察领先关系何时持续收窄或扩大，而不是只比较最终终点。"],
  },
  "dow-century": {
    title: "道琼斯价格指数（1992 年以来）",
    dataPath: "/data/dji_century.json",
    kind: "price",
    scaleType: "log",
    yUnit: "指数点位",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "dow-annual": {
    title: "道琼斯年度回报",
    dataPath: "/data/dji_annual.json",
    kind: "annual",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "dow-drawdowns": {
    title: "道琼斯主要历史回撤的跌幅与修复时间",
    dataPath: "/data/dji_drawdowns.json",
    kind: "drawdown",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },

  // ─── Valuation ───
  "shiller-cape": {
    title: "当前 CAPE 处在怎样的历史位置？",
    dataPath: "/data/shiller_cape.json",
    description:
      "CAPE 用过去十年经通胀调整的平均盈利，降低单一经济周期的噪音。",
    interpretation: [
      "高历史分位表示市场为平滑盈利支付更高价格，不代表马上下跌。",
    ],
    kind: "multiline",
    source: "Robert J. Shiller, Yale University",
    eyebrow: "SHILLER CAPE · 1871→",
    series: [{ key: "cape", label: "CAPE (P/E10)", unit: "倍" }],
    whatToWatch: [
      "价格与十年平均盈利的相对变化，以及当前分位能否被盈利增长消化。",
    ],
  },
  "shiller-pe": {
    title: "市场为最近十二个月盈利支付多少倍价格？",
    dataPath: "/data/shiller_cape.json",
    description:
      "TTM PE 使用最近十二个月盈利，比 CAPE 更敏感，也更受经济周期影响。",
    interpretation: [
      "PE 上升可能来自价格上涨，也可能来自盈利下降，两种情况含义不同。",
    ],
    kind: "multiline",
    source: "Robert J. Shiller, Yale University",
    eyebrow: "TTM PE · 1871→",
    series: [{ key: "pe_ttm", label: "PE (TTM)", unit: "倍" }],
    whatToWatch: ["把 PE 变化与同页 EPS 同时核对。"],
  },
  "shiller-eps": {
    title: "S&P 500 每股盈利的长期增长路径",
    dataPath: "/data/shiller_cape.json",
    description: "指数层面最近十二个月每股盈利，展示长期回报背后的盈利基础。",
    interpretation: ["长期价格增长需要盈利增长支撑，短期两者可以明显背离。"],
    kind: "multiline",
    source: "Robert J. Shiller, Yale University",
    eyebrow: "EARNINGS · 1871→",
    series: [{ key: "eps", label: "EPS (TTM)", unit: "美元" }],
    whatToWatch: ["盈利是否继续增长，以及价格增速是否长期快于盈利。"],
  },
  vxn: {
    title: "VXN 怎样反映 Nasdaq-100 的风险价格？",
    dataPath: "/data/vxn.json",
    description: "VXN 是基于 Nasdaq-100 期权价格计算的三十日隐含波动率指数。",
    interpretation: [
      "VXN 上升表示期权市场提高了未来波动定价，不直接表示指数方向。",
    ],
    kind: "valuation",
    valueKey: "close",
    valueLabel: "VXN",
    source: "Cboe Global Markets",
    eyebrow: "NASDAQ-100 IMPLIED VOLATILITY",
    whatToWatch: [
      "比较 VXN 的持续时间，并与 Nasdaq-100 实现波动和回撤同步核对。",
    ],
  },
  "mag7-weight": {
    title: "七巨头在 S&P 500 中占多少权重？",
    dataPath: "/data/mag7_weight.json",
    kind: "multiline",
    source: "Yahoo Finance · ArcOfMarket 计算",
    eyebrow: "CONCENTRATION",
    series: [{ key: "weight_pct", label: "七巨头合计占比", unit: "%" }],
  },
} as const satisfies ChartIndex;
