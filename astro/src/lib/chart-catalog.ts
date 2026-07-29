import { resolveChartSpec, type ChartKey } from "@/content/chart-copy";
import { pageContent, type ContentPageKey } from "@/content/page-content";
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

function entry(title: string, description: string, href: string): ChartEntry {
  return { description, href, title };
}

function schemaChartEntries(pageKey: ContentPageKey): ChartEntry[] {
  const page = pageContent[pageKey];
  return page.chapters.flatMap((chapter) =>
    chapter.blocks.flatMap((block) => {
      if (block.type !== "chart") return [];
      const spec = resolveChartSpec(block.chart as ChartKey);
      return [entry(spec.title, spec.description, `${page.route}#${spec.id}`)];
    }),
  );
}

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

const macroCharts = [
  entry("SOFR × EFFR × 目标利率", "美国短端资金价格。", "/macro/#macro-policy-rates"),
  entry("期限结构", "2Y、10Y、20Y 与 30Y 国债收益率。", "/macro/#macro-term-structure"),
  entry("10Y − 2Y 期限利差", "曲线倒挂与再陡峭化。", "/macro/#macro-yield-spread"),
  entry("CPI × 核心 PCE × PPI", "不同通胀口径的路径。", "/macro/#macro-prices"),
  entry("实际 GDP", "季度增长的年化读数。", "/macro/#macro-gdp"),
  entry("就业", "非农新增与失业率。", "/macro/#macro-employment"),
  entry(
    "股票配置占比",
    "美国金融资产中的股票配置比例。",
    "/macro/#macro-equity-allocation",
  ),
  entry("OFR 金融压力", "信用、融资、波动和安全资产压力。", "/macro/#stress-title"),
  entry("CFTC VIX 仓位", "带发布时间快照的期货净头寸。", "/macro/#macro-positioning"),
];

const sp500Components = [
  entry("S&P 500 当前横截面", "按市值与当日涨跌观察指数内部。", "/sp500/#sp500-cross-section"),
  entry("行业与成分结构", "核对当前行业分布和成分公司。", "/sp500/#composition-title"),
  entry("成分变更", "公开可追溯的调入与剔除。", "/sp500/#changes-title"),
];

const nasdaqComponents = [
  entry("Nasdaq-100 当前横截面", "按市值与当日涨跌观察头部权重。", "/nasdaq/#ndx-cross-section"),
  entry("Nasdaq-100 成分排名", "比较一周、一月、年内和一年回报。", "/nasdaq/#ndx-rankings"),
];

const mag7Charts = [
  entry("七巨头等权篮子", "与 S&P 500 和 Nasdaq-100 比较。", "/magnificent-seven/#mag7-equal-weight"),
  entry("七巨头指数权重", "七家公司合计占 S&P 500 的比例。", "/magnificent-seven/#mag7-weight"),
  entry("七家公司回报", "把成员归一化到同一起点。", "/magnificent-seven/#mag7-members"),
  entry("七家公司回撤", "当前回撤与历史最大回撤。", "/magnificent-seven/#mag7-drawdowns"),
  entry(
    "七家公司相关性",
    "比较七家公司日回报的 60 日滚动平均相关系数。",
    "/magnificent-seven/#mag7-correlation",
  ),
  entry("科技龙头谱系", "从 Nifty Fifty 到 Magnificent Seven。", "/magnificent-seven/#mag7-lineage"),
  entry("Nvidia 与 Cisco 估值", "比较两个算力投资周期的估值。", "/magnificent-seven/#mag7-nvda-cisco"),
];

export const chartGroups: readonly ChartGroup[] = [
  {
    charts: macroCharts,
    code: "MACRO",
    description: "资金价格、通胀、增长、仓位和金融压力。",
    href: "/macro/",
    title: "宏观",
  },
  {
    charts: [...schemaChartEntries("sp500"), ...sp500Components],
    code: "SPX",
    description: "长期回报、估值、风险、广度和指数结构。",
    href: "/sp500/",
    title: "标普 500",
  },
  {
    charts: [...schemaChartEntries("nasdaq"), ...nasdaqComponents],
    code: "NDX",
    description: "综合指数与 Nasdaq-100 的回报、风险、估值和广度。",
    href: "/nasdaq/",
    title: "纳斯达克",
  },
  {
    charts: schemaChartEntries("dow"),
    code: "DJI",
    description: "蓝筹、全市场和成长风格的长期对比。",
    href: "/dow/",
    title: "道琼斯",
  },
  {
    charts: mag7Charts,
    code: "M7",
    description: "头部科技公司的集中度、成员分化、相关性和历史谱系。",
    href: "/magnificent-seven/",
    title: "七巨头",
  },
  {
    charts: sectorCharts,
    code: "SECTORS",
    description: "行业、子行业和代表性公司的横向比较。",
    href: "/sectors/",
    title: "行业板块",
  },
  {
    charts: [
      entry("市场环境总览", "利率、压力、风险偏好与宽度摘要。", "/lab/#market-environment"),
      entry("主要指数与 ETF", "SPY、QQQ、VOO 与 VTV。", "/lab/#market-index-etfs"),
      entry("市值加权热力图", "成分涨跌与权重的横截面。", "/lab/#market-heatmap"),
    ],
    code: "LAB",
    description: "市场底图、主要 ETF 与当日横截面。",
    href: "/lab/",
    title: "实验室指标",
  },
];

export const chartCount = chartGroups.reduce(
  (total, group) => total + group.charts.length,
  0,
);
