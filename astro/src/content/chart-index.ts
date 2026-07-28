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
    title: "一百年，画在这一张图上",
    dataPath: "/data/sp500_century.json",
    kind: "price",
    scaleType: "log",
    yUnit: "指数点位",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-total-return": {
    title: "三分之二的回报来自股息——但你只看价格的话，根本看不见",
    dataPath: "/data/sp500_total_return.json",
    kind: "valuation",
    scaleType: "log",
    yUnit: "指数点位",
    valueKey: "values",
    valueLabel: "总回报指数",
    source: "Yahoo Finance · S&P 500 Total Return Index",
  },
  "sp500-annual": {
    title: "98 份年度成绩单——73 年赚、26 年亏",
    dataPath: "/data/sp500_annual.json",
    kind: "annual",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-bullbear": {
    title: "牛市走多久，熊市跌多深",
    dataPath: "/data/sp500_bullbear.json",
    kind: "cycles",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-extremes": {
    title: "最好的日子和最坏的日子——往往挨在一起",
    dataPath: "/data/sp500_extremes.json",
    kind: "extremes",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-distribution": {
    title: "平均 11.8%——但几乎没有一个年份刚好落在这个数上",
    dataPath: "/data/sp500_distribution.json",
    kind: "distribution",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-holding": {
    title: "持有多久，几乎不会亏？",
    dataPath: "/data/sp500_holding.json",
    kind: "holding",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-rollmatrix": {
    title: "同一笔钱，入场时间不同，结果天差地别",
    dataPath: "/data/sp500_rollmatrix.json",
    kind: "rollmatrix",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-rolling5y": {
    title: "任意时点买、拿满五年——年化回报跑到了哪",
    dataPath: "/data/sp500_rolling5y.json",
    kind: "rolling",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-intrayear": {
    title: "每年都跌过——跌了就跑，你可能错过了最贵的反弹",
    dataPath: "/data/sp500_intrayear.json",
    kind: "intrayear",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-seasonality": {
    title: "十二个月的脾气——哪个月最顺，哪个月最凶",
    dataPath: "/data/sp500_seasonality.json",
    kind: "seasonality",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-drawdowns": {
    title: "每一次深跌都有名字——跌了多少，花了多久爬回来",
    dataPath: "/data/sp500_drawdowns.json",
    kind: "drawdown",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "sp500-volatility": {
    title: "市场的呼吸频率——紧张的时候就快，平静的时候就慢",
    dataPath: "/data/sp500_volatility.json",
    kind: "volatility",
    source: "Yahoo Finance 历史价格 · Cboe · ArcOfMarket 计算",
  },
  "sp500-vol-family": {
    title: "恐慌的价目表——不同期限的保险费",
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
    title: "市值 · 回报 · 指数权重",
    dataPath: "", // TradingView heatmap, no data file
    kind: "price",
    source: "TradingView SPX500",
  },
  "sp500-changes": {
    title: "调入与调出的历史",
    dataPath: "/data/sp500_changes.json",
    kind: "changes",
    source: "Wikipedia 固定版本 · CC BY-SA 4.0",
  },

  // ─── Nasdaq Composite ───
  "ixic-century": {
    title: "半个世纪的成长与泡沫——从 100 点到一万六千点",
    dataPath: "/data/ixic_century.json",
    kind: "price",
    scaleType: "log",
    yUnit: "指数点位",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-annual": {
    title: "成长股的年度成绩单——涨得比标普多，跌得也比标普狠",
    dataPath: "/data/ixic_annual.json",
    kind: "annual",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-bullbear": {
    title: "纳指的牛熊——更陡的上涨，更深的坠落",
    dataPath: "/data/ixic_bullbear.json",
    kind: "cycles",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-extremes": {
    title: "成长股的极端日——疯狂起来比大盘更疯",
    dataPath: "/data/ixic_extremes.json",
    kind: "extremes",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-distribution": {
    title: "成长股的年份分布——好年真好，坏年真坏",
    dataPath: "/data/ixic_distribution.json",
    kind: "distribution",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-holding": {
    title: "拿着纳斯达克，多久才能睡得着？",
    dataPath: "/data/ixic_holding.json",
    kind: "holding",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-rollmatrix": {
    title: "同一笔钱，不同时点进场——结果差距有多大",
    dataPath: "/data/ixic_rollmatrix.json",
    kind: "rollmatrix",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-rolling5y": {
    title: "任意时点买、拿满五年——dotcom 之后十年年化曾经归零",
    dataPath: "/data/ixic_rolling5y.json",
    kind: "rolling",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-intrayear": {
    title: "成长股每年都跌——只是跌多跌少的问题",
    dataPath: "/data/ixic_intrayear.json",
    kind: "intrayear",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-seasonality": {
    title: "纳指的十二个月——哪个月友好，哪个月残酷",
    dataPath: "/data/ixic_seasonality.json",
    kind: "seasonality",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-drawdowns": {
    title: "2000 年跌了 78%——每一次都有人说是“这次不一样”",
    dataPath: "/data/ixic_drawdowns.json",
    kind: "drawdown",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ixic-volatility": {
    title: "成长股的心跳——系统性更快、更猛",
    dataPath: "/data/ixic_volatility.json",
    kind: "volatility",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },

  // ─── Nasdaq-100 ───
  "ndx-century": {
    title: "最大的 100 家非金融公司——从 1985 年一路走到今天",
    dataPath: "/data/ndx_century.json",
    kind: "price",
    scaleType: "log",
    yUnit: "指数点位",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-annual": {
    title: "Nasdaq-100 的年度成绩单",
    dataPath: "/data/ndx_annual.json",
    kind: "annual",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-bullbear": {
    title: "科技龙头的牛熊——dotcom 崩了 83%",
    dataPath: "/data/ndx_bullbear.json",
    kind: "cycles",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-extremes": {
    title: "科技股最疯的日子和最惨的日子",
    dataPath: "/data/ndx_extremes.json",
    kind: "extremes",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-distribution": {
    title: "Nasdaq-100 年度回报的真实分布",
    dataPath: "/data/ndx_distribution.json",
    kind: "distribution",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-holding": {
    title: "拿着 Nasdaq-100，多久能赚钱？",
    dataPath: "/data/ndx_holding.json",
    kind: "holding",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-rollmatrix": {
    title: "入场时点对了还是错了——一目了然",
    dataPath: "/data/ndx_rollmatrix.json",
    kind: "rollmatrix",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-rolling5y": {
    title: "五年之后回头看——年化回报跑到了哪",
    dataPath: "/data/ndx_rolling5y.json",
    kind: "rolling",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-intrayear": {
    title: "科技股每年都回撤——跌了就跑是最贵的策略",
    dataPath: "/data/ndx_intrayear.json",
    kind: "intrayear",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-seasonality": {
    title: "Nasdaq-100 十二个月的脾气",
    dataPath: "/data/ndx_seasonality.json",
    kind: "seasonality",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-drawdowns": {
    title: "Nasdaq-100 经历过的每一次深跌",
    dataPath: "/data/ndx_drawdowns.json",
    kind: "drawdown",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-volatility": {
    title: "科技股的呼吸频率——系统性比大盘快",
    dataPath: "/data/ndx_volatility.json",
    kind: "volatility",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "ndx-cross-section": {
    title: "头部持仓与累计权重",
    dataPath: "",
    kind: "price",
    source: "TradingView NASDAQ100",
  },
  "ndx-valuation-proxy": {
    title: "纳指 100 动态估值代理",
    dataPath: "/data/ndx_valuation_proxy.json",
    kind: "multiline",
    source: "Yahoo Finance QQQ 基本面元数据",
    note: "这是 QQQ trailing PE 代理，不是 Nasdaq 官方 NDX PE，也不是 Forward PE。",
    series: [{ key: "trailing_pe", label: "QQQ TTM PE", unit: "倍" }],
  },

  // ─── Macro ───
  "macro-credit": {
    title: "信用利差",
    dataPath: "/data/macro_credit.json",
    kind: "nested",
    source: "FRED · ICE Data Indices",
    series: [
      { key: "hy_oas", label: "高收益 OAS", unit: "%" },
      { key: "ig_oas", label: "投资级 OAS", unit: "%" },
    ],
  },

  // ─── Mag7 ───
  "mag7-equal-weight": {
    title: "七巨头等权指数",
    dataPath: "/data/mag7_equal_weight.json",
    kind: "price",
    source: "Yahoo Finance · ArcOfMarket 计算",
    eyebrow: "EQUAL-WEIGHT BASKET",
  },
  "mag7-prices": {
    title: "七家公司归一化价格",
    dataPath: "/data/mag7_prices.json",
    kind: "price",
    source: "Yahoo Finance · ArcOfMarket 计算",
    eyebrow: "NORMALIZED COMPARISON",
  },
  "mag7-valuation": {
    title: "Nvidia vs Cisco TTM PE",
    dataPath: "/data/nvda_csco_valuation.json",
    kind: "multiline",
    source: "Yahoo Finance 基本面元数据 · ArcOfMarket 积累",
    eyebrow: "VALUATION ANCHOR",
  },

  // ─── Dow ───
  "dow-etf-proxies": {
    title: "三种美国，三条线——旧经济 vs 全市场 vs 新经济",
    dataPath: "/data/etf_proxies.json",
    kind: "price",
    source: "Yahoo Finance · ArcOfMarket 计算",
    eyebrow: "BENCHMARK COMPARISON",
  },
  "dow-century": {
    title: "从 66 点到三万点——道琼斯的世纪之旅",
    dataPath: "/data/dji_century.json",
    kind: "price",
    scaleType: "log",
    yUnit: "指数点位",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "dow-annual": {
    title: "道琼斯的年度成绩单",
    dataPath: "/data/dji_annual.json",
    kind: "annual",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },
  "dow-drawdowns": {
    title: "大萧条跌了 89%——道琼斯经历过的最深伤疤",
    dataPath: "/data/dji_drawdowns.json",
    kind: "drawdown",
    source: "Yahoo Finance 历史价格 · ArcOfMarket 计算",
  },

  // ─── Valuation ───
  "shiller-cape": {
    title: "席勒 CAPE——现在到底贵不贵？",
    dataPath: "/data/shiller_cape.json",
    kind: "multiline",
    source: "Robert J. Shiller, Yale University",
    eyebrow: "SHILLER CAPE · 1871→",
    series: [
      { key: "cape", label: "CAPE (P/E10)", unit: "倍" },
    ],
  },
  "shiller-pe": {
    title: "TTM PE——市场对当前盈利愿意付多少钱",
    dataPath: "/data/shiller_cape.json",
    kind: "multiline",
    source: "Robert J. Shiller, Yale University",
    eyebrow: "TTM PE · 1871→",
    series: [
      { key: "pe_ttm", label: "PE (TTM)", unit: "倍" },
    ],
  },
  "shiller-eps": {
    title: "指数背后——每股盈利涨了多少",
    dataPath: "/data/shiller_cape.json",
    kind: "multiline",
    source: "Robert J. Shiller, Yale University",
    eyebrow: "EARNINGS · 1871→",
    series: [
      { key: "eps", label: "EPS (TTM)", unit: "美元" },
    ],
  },
  "vxn": {
    title: "纳斯达克的恐慌指数——比 VIX 更快的心跳",
    dataPath: "/data/vxn.json",
    kind: "valuation",
    valueKey: "close",
    valueLabel: "VXN",
    source: "Cboe Global Markets",
    eyebrow: "NASDAQ FEAR INDEX",
  },
  "mag7-weight": {
    title: "七家公司，占了标普的三分之一",
    dataPath: "/data/mag7_weight.json",
    kind: "multiline",
    source: "Yahoo Finance · ArcOfMarket 计算",
    eyebrow: "CONCENTRATION",
    series: [
      { key: "weight_pct", label: "七巨头合计占比", unit: "%" },
    ],
  },
} as const satisfies ChartIndex;
