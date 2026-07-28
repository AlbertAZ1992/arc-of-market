import { marketThemes } from "@/lib/market-themes";

export type ChartEntry = {
  description: string;
  href: string;
  title: string;
};

export type ChartGroup = {
  charts: readonly ChartEntry[];
  code: string;
  description: string;
  href: string;
  title: string;
};

const entry = (
  title: string,
  description: string,
  href: string,
): ChartEntry => ({ description, href, title });

const extendedSectorCharts = marketThemes
  .filter(
    (theme) =>
      ![
        "semiconductors",
        "information-technology",
        "financials",
        "consumer",
      ].includes(theme.slug),
  )
  .flatMap((theme) =>
    theme.groups.map((group, index) =>
      entry(
        `${theme.title.split("：")[0]} · ${group.heading}`,
        group.description,
        `/themes/${theme.slug}/#theme-group-${index + 1}`,
      ),
    ),
  );

const sectorCharts = [
  entry(
    "半导体行业代理",
    "SMH 与 SOXX 的周期路径。",
    "/themes/semiconductors/#theme-group-1",
  ),
  entry(
    "领涨与落后",
    "设计、制造、设备和存储分化。",
    "/themes/semiconductors/#theme-group-2",
  ),
  entry(
    "信息科技板块与子行业",
    "XLK、软件、云和网络安全代理。",
    "/themes/information-technology/#theme-group-1",
  ),
  entry(
    "软件、云与安全",
    "细分 ETF 与核心公司。",
    "/themes/information-technology/#theme-group-2",
  ),
  entry(
    "金融板块与子行业",
    "XLF、银行、区域银行和保险代理。",
    "/themes/financials/#theme-group-1",
  ),
  entry(
    "金融核心公司",
    "大行、投行、资管、券商和支付网络。",
    "/themes/financials/#theme-group-2",
  ),
  entry(
    "2008 金融危机横截面",
    "银行、保险与券商的路径。",
    "/themes/financials/#financial-crisis-2008",
  ),
  entry(
    "必需消费",
    "XLP 与核心防守型消费公司。",
    "/themes/consumer/#theme-group-1",
  ),
  entry(
    "XLP × XLY",
    "防守与周期消费的相对强弱。",
    "/themes/consumer/#consumer-xlp-xly",
  ),
  entry(
    "零售与住宅链",
    "XRT、XHB 与核心公司。",
    "/themes/consumer/#theme-group-2",
  ),
  ...extendedSectorCharts,
];

export const chartGroups: readonly ChartGroup[] = [
  {
    code: "MACRO",
    title: "宏观",
    description: "先判断资金价格、物价、增长、仓位和金融压力。",
    href: "/macro/",
    charts: [
      entry(
        "SOFR × EFFR × 目标利率",
        "美国资金价格。",
        "/macro/#macro-policy-rates",
      ),
      entry(
        "期限结构",
        "2Y、10Y、20Y 与 30Y 国债收益率。",
        "/macro/#macro-term-structure",
      ),
      entry(
        "10Y − 2Y 期限利差",
        "曲线倒挂与再陡峭化。",
        "/macro/#macro-yield-spread",
      ),
      entry(
        "CPI × 核心 PCE × PPI",
        "不同通胀口径的路径。",
        "/macro/#macro-prices",
      ),
      entry("实际 GDP", "季度增长的年化读数。", "/macro/#macro-gdp"),
      entry("就业", "非农新增与失业率。", "/macro/#macro-employment"),
      entry(
        "股票配置占比",
        "美国金融资产中的股票配置比例。",
        "/macro/#macro-equity-allocation",
      ),
      entry("OFR 金融压力", "信用、融资与波动压力。", "/macro/#stress-title"),
      entry(
        "CFTC VIX 仓位",
        "带发布时间快照的期货净头寸。",
        "/macro/#macro-positioning",
      ),
      entry("信用利差", "高收益与投资级 OAS。", "/macro/#macro-credit"),
    ],
  },
  {
    code: "SPX",
    title: "标普 500",
    description: "再看大盘指数的长期回报、估值、风险和内部结构。",
    href: "/sp500/",
    charts: [
      entry(
        "世纪尺度下的美股",
        "长期价格、通胀与衰退区间。",
        "/sp500/#sp500-century",
      ),
      entry(
        "S&P 500 总回报指数",
        "把股息再投资纳入长期回报。",
        "/sp500/#sp500-total-return",
      ),
      entry(
        "S&P 500 年度回报",
        "每个自然年的价格回报。",
        "/sp500/#sp500-annual",
      ),
      entry(
        "S&P 500 牛熊周期",
        "周期涨跌幅与持续时间。",
        "/sp500/#sp500-bullbear",
      ),
      entry(
        "S&P 500 极端交易日",
        "历史最佳与最差单日。",
        "/sp500/#sp500-extremes",
      ),
      entry(
        "S&P 500 年度回报分布",
        "常见区间与尾部年份。",
        "/sp500/#sp500-distribution",
      ),
      entry(
        "S&P 500 持有期结果",
        "胜率与中位年化回报。",
        "/sp500/#sp500-holding",
      ),
      entry(
        "S&P 500 多周期滚动回报",
        "五年、十年与二十年。",
        "/sp500/#sp500-rollmatrix",
      ),
      entry(
        "S&P 500 滚动五年回报",
        "五年年化回报路径。",
        "/sp500/#sp500-rolling5y",
      ),
      entry(
        "年内回撤与年度结果",
        "年内最大跌幅与全年回报。",
        "/sp500/#sp500-intrayear",
      ),
      entry(
        "S&P 500 月份季节性",
        "平均回报与上涨概率。",
        "/sp500/#sp500-seasonality",
      ),
      entry(
        "S&P 500 历史回撤",
        "深度、时长与修复。",
        "/sp500/#sp500-drawdowns",
      ),
      entry("S&P 500 波动率", "实现波动率与 VIX。", "/sp500/#sp500-volatility"),
      entry(
        "VIX 期限家族与 SKEW",
        "从九日到一年期的波动结构。",
        "/sp500/#sp500-vol-family",
      ),
      entry(
        "市值 · 一年回报 · 指数权重",
        "当前成分横截面气泡图。",
        "/sp500/#sp500-cross-section",
      ),
      entry(
        "GICS 行业结构",
        "当前成分与行业家数。",
        "/sp500/#composition-title",
      ),
      entry(
        "当前成分目录",
        "按代码、公司与行业检索。",
        "/sp500/#directory-title",
      ),
      entry(
        "调入与调出的历史",
        "公开可追溯的成分变更事件。",
        "/sp500/#sp500-anatomy",
      ),
    ],
  },
  {
    code: "NDX",
    title: "纳斯达克",
    description: "观察大型成长、科技权重与纳斯达克市场代理。",
    href: "/nasdaq/",
    charts: [
      entry(
        "纳斯达克综合指数",
        "半个世纪的成长与泡沫。",
        "/nasdaq/#nasdaq-composite-suite",
      ),
      entry(
        "综合指数长期价格",
        "整个纳斯达克市场的长期坐标。",
        "/nasdaq/#ixic-century",
      ),
      entry(
        "综合指数年度回报",
        "每个自然年的价格回报。",
        "/nasdaq/#ixic-annual",
      ),
      entry(
        "综合指数牛熊周期",
        "周期涨跌幅与持续时间。",
        "/nasdaq/#ixic-bullbear",
      ),
      entry(
        "综合指数极端交易日",
        "历史最佳与最差单日。",
        "/nasdaq/#ixic-extremes",
      ),
      entry(
        "综合指数年度分布",
        "常见区间与尾部年份。",
        "/nasdaq/#ixic-distribution",
      ),
      entry(
        "综合指数持有期结果",
        "胜率与中位年化回报。",
        "/nasdaq/#ixic-holding",
      ),
      entry(
        "综合指数多周期回报",
        "五年、十年与二十年。",
        "/nasdaq/#ixic-rollmatrix",
      ),
      entry(
        "综合指数滚动五年回报",
        "五年年化回报路径。",
        "/nasdaq/#ixic-rolling5y",
      ),
      entry(
        "综合指数年内回撤",
        "年内最大跌幅与全年回报。",
        "/nasdaq/#ixic-intrayear",
      ),
      entry(
        "综合指数月份季节性",
        "平均回报与上涨概率。",
        "/nasdaq/#ixic-seasonality",
      ),
      entry(
        "综合指数历史回撤",
        "深度、时长与修复。",
        "/nasdaq/#ixic-drawdowns",
      ),
      entry(
        "综合指数实现波动",
        "二十日与六十日实现波动。",
        "/nasdaq/#ixic-volatility",
      ),
      entry(
        "Nasdaq-100 长期价格",
        "大型非金融公司的长期坐标。",
        "/nasdaq/#ndx-century",
      ),
      entry(
        "Nasdaq-100 年度回报",
        "每个自然年的价格回报。",
        "/nasdaq/#ndx-annual",
      ),
      entry(
        "Nasdaq-100 牛熊周期",
        "周期涨跌幅与持续时间。",
        "/nasdaq/#ndx-bullbear",
      ),
      entry(
        "Nasdaq-100 极端交易日",
        "历史最佳与最差单日。",
        "/nasdaq/#ndx-extremes",
      ),
      entry(
        "Nasdaq-100 年度分布",
        "常见区间与尾部年份。",
        "/nasdaq/#ndx-distribution",
      ),
      entry(
        "Nasdaq-100 持有期结果",
        "胜率与中位年化回报。",
        "/nasdaq/#ndx-holding",
      ),
      entry(
        "Nasdaq-100 多周期回报",
        "五年、十年与二十年。",
        "/nasdaq/#ndx-rollmatrix",
      ),
      entry(
        "Nasdaq-100 滚动五年回报",
        "五年年化回报路径。",
        "/nasdaq/#ndx-rolling5y",
      ),
      entry(
        "Nasdaq-100 年内回撤",
        "年内最大跌幅与全年回报。",
        "/nasdaq/#ndx-intrayear",
      ),
      entry(
        "Nasdaq-100 月份季节性",
        "平均回报与上涨概率。",
        "/nasdaq/#ndx-seasonality",
      ),
      entry(
        "Nasdaq-100 历史回撤",
        "深度、时长与修复。",
        "/nasdaq/#ndx-drawdowns",
      ),
      entry(
        "Nasdaq-100 实现波动",
        "二十日与六十日实现波动。",
        "/nasdaq/#ndx-volatility",
      ),
      entry(
        "头部持仓与累计权重",
        "集中度与成分结构。",
        "/nasdaq/#ndx-cross-section",
      ),
      entry(
        "纳指 100 动态估值代理",
        "每日积累 QQQ 滚动市盈率。",
        "/nasdaq/#ndx-dynamic-pe",
      ),
    ],
  },
  {
    code: "DJI",
    title: "道琼斯",
    description: "用可交易代理观察蓝筹风格与行业暴露。",
    href: "/dow/",
    charts: [
      entry("道琼斯与大盘", "DIA、SPY 与 QQQ 的价格对照。", "/dow/#section-1"),
      entry("蓝筹行业暴露", "工业、金融与消费板块代理。", "/dow/#section-2"),
    ],
  },
  {
    code: "M7",
    title: "七巨头",
    description: "观察头部科技公司的整体路径、集中度和成员分化。",
    href: "/magnificent-seven/",
    charts: [
      entry(
        "Magnificent 7 等权代理",
        "七巨头 ETF 与大盘对照。",
        "/magnificent-seven/#mag7-equal-weight",
      ),
      entry(
        "七家公司成员分化",
        "逐一观察七家公司价格路径。",
        "/magnificent-seven/#mag7-members",
      ),
      entry(
        "NVDA 与 1999 Cisco",
        "两个算力周期的历史类比。",
        "/magnificent-seven/#mag7-nvda-cisco",
      ),
    ],
  },
  {
    code: "SECTORS",
    title: "行业板块",
    description: "再进入行业、子行业和代表性公司的横向比较。",
    href: "/sectors/",
    charts: sectorCharts,
  },
  {
    code: "LAB",
    title: "实验室指标",
    description: "最后查看市场底图、主要 ETF 与当日横截面。",
    href: "/lab/",
    charts: [
      entry(
        "市场环境总览",
        "利率、压力、风险偏好与宽度摘要。",
        "/lab/#market-environment",
      ),
      entry(
        "主要指数与 ETF",
        "SPY、QQQ、VOO 与 VTV 的公开组件视图。",
        "/lab/#market-index-etfs",
      ),
      entry(
        "市值加权热力图",
        "成分涨跌与权重的横截面。",
        "/lab/#market-heatmap",
      ),
    ],
  },
] as const;

export const chartCount = chartGroups.reduce(
  (total, group) => total + group.charts.length,
  0,
);
