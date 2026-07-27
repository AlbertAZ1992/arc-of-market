export type SymbolDefinition = readonly [label: string, symbol: string];

export type MarketTheme = {
  slug: string;
  eyebrow: string;
  title: string;
  description: string;
  groups: readonly {
    heading: string;
    description: string;
    symbols: readonly SymbolDefinition[];
  }[];
};

export const marketThemes = [
  {
    slug: "information-technology",
    eyebrow: "INFORMATION TECHNOLOGY",
    title: "信息科技：软件、云与安全",
    description: "先看科技板块与软件、云、安全代理，再观察核心公司的分化。",
    groups: [
      {
        heading: "板块与子行业代理",
        description:
          "XLK 是信息科技锚；IGV、SKYY 与 CIBR 分别观察软件、云和网络安全。",
        symbols: [
          ["信息科技 XLK", "AMEX:XLK|1D"],
          ["软件 IGV", "AMEX:IGV|1D"],
          ["云计算 SKYY", "NASDAQ:SKYY|1D"],
          ["网络安全 CIBR", "NASDAQ:CIBR|1D"],
        ],
      },
      {
        heading: "核心公司",
        description: "并列核心公司的价格路径，观察成员之间何时同步、何时分化。",
        symbols: [
          ["Apple", "NASDAQ:AAPL|1D"],
          ["Microsoft", "NASDAQ:MSFT|1D"],
          ["Oracle", "NYSE:ORCL|1D"],
          ["Salesforce", "NYSE:CRM|1D"],
          ["ServiceNow", "NYSE:NOW|1D"],
          ["Adobe", "NASDAQ:ADBE|1D"],
        ],
      },
    ],
  },
  {
    slug: "semiconductors",
    eyebrow: "SEMICONDUCTORS",
    title: "半导体：算力与周期",
    description:
      "用两只行业 ETF 和主要芯片公司观察算力主线、设备周期与成员分化。",
    groups: [
      {
        heading: "行业代理",
        description:
          "SMH 与 SOXX 的编制并不相同，并列观察可以减少单一 ETF 权重结构的偏差。",
        symbols: [
          ["VanEck Semiconductor ETF", "NASDAQ:SMH|1D"],
          ["iShares Semiconductor ETF", "NASDAQ:SOXX|1D"],
        ],
      },
      {
        heading: "产业链核心公司",
        description:
          "覆盖设计、代工、设备与存储；币种和交易所差异由 TradingView 标示。",
        symbols: [
          ["Nvidia", "NASDAQ:NVDA|1D"],
          ["Broadcom", "NASDAQ:AVGO|1D"],
          ["TSMC", "NYSE:TSM|1D"],
          ["AMD", "NASDAQ:AMD|1D"],
          ["Micron", "NASDAQ:MU|1D"],
          ["ASML", "NASDAQ:ASML|1D"],
          ["Sandisk", "NASDAQ:SNDK|1D"],
        ],
      },
    ],
  },
  {
    slug: "financials",
    eyebrow: "FINANCIALS & FINTECH",
    title: "金融：银行、保险与资本市场",
    description: "从 XLF 到银行、区域银行、保险，再到卡组织、券商与金融科技。",
    groups: [
      {
        heading: "板块与子行业代理",
        description:
          "XLF 是金融锚；KBE、KRE、KIE 分别观察银行、区域银行和保险。",
        symbols: [
          ["金融 XLF", "AMEX:XLF|1D"],
          ["银行 KBE", "AMEX:KBE|1D"],
          ["区域银行 KRE", "AMEX:KRE|1D"],
          ["保险 KIE", "AMEX:KIE|1D"],
        ],
      },
      {
        heading: "核心公司",
        description: "覆盖大行、投行、资管、券商、卡组织与上市金融科技平台。",
        symbols: [
          ["JPMorgan", "NYSE:JPM|1D"],
          ["Bank of America", "NYSE:BAC|1D"],
          ["Goldman Sachs", "NYSE:GS|1D"],
          ["Morgan Stanley", "NYSE:MS|1D"],
          ["BlackRock", "NYSE:BLK|1D"],
          ["Charles Schwab", "NYSE:SCHW|1D"],
          ["Visa", "NYSE:V|1D"],
          ["Mastercard", "NYSE:MA|1D"],
          ["Coinbase", "NASDAQ:COIN|1D"],
          ["Robinhood", "NASDAQ:HOOD|1D"],
        ],
      },
    ],
  },
  {
    slug: "consumer",
    eyebrow: "CONSUMER",
    title: "消费：防守与周期",
    description: "把必需消费、可选消费、零售与住宅链放在同一套观察框架中。",
    groups: [
      {
        heading: "必需消费",
        description: "XLP 是防守型消费锚，再观察品牌、商超和会员制零售的分化。",
        symbols: [
          ["必需消费 XLP", "AMEX:XLP|1D"],
          ["Coca-Cola", "NYSE:KO|1D"],
          ["Walmart", "NASDAQ:WMT|1D"],
          ["Costco", "NASDAQ:COST|1D"],
          ["Procter & Gamble", "NYSE:PG|1D"],
          ["Philip Morris", "NYSE:PM|1D"],
        ],
      },
      {
        heading: "可选消费、零售与住宅链",
        description: "XLY、XRT 与 XHB 分别观察可选消费、零售广度和住宅链。",
        symbols: [
          ["可选消费 XLY", "AMEX:XLY|1D"],
          ["零售 XRT", "AMEX:XRT|1D"],
          ["住宅建筑 XHB", "AMEX:XHB|1D"],
          ["Amazon", "NASDAQ:AMZN|1D"],
          ["Home Depot", "NYSE:HD|1D"],
          ["TJX", "NYSE:TJX|1D"],
          ["McDonald's", "NYSE:MCD|1D"],
        ],
      },
    ],
  },
  {
    slug: "communication-services",
    eyebrow: "COMMUNICATION SERVICES",
    title: "通信服务：平台、内容与网络",
    description:
      "用 XLC 观察平台与内容权重，再拆分流媒体、广告平台和电信网络。",
    groups: [
      {
        heading: "板块与子行业代理",
        description: "XLC 是通信服务锚；VOX 与 FCOM 提供不同发行人的编制对照。",
        symbols: [
          ["通信服务 XLC", "AMEX:XLC|1D"],
          ["Vanguard 通信 VOX", "AMEX:VOX|1D"],
          ["Fidelity 通信 FCOM", "AMEX:FCOM|1D"],
        ],
      },
      {
        heading: "平台、内容与网络",
        description: "覆盖数字广告、社交平台、流媒体、传统内容和电信运营商。",
        symbols: [
          ["Alphabet", "NASDAQ:GOOGL|1D"],
          ["Meta", "NASDAQ:META|1D"],
          ["Netflix", "NASDAQ:NFLX|1D"],
          ["Disney", "NYSE:DIS|1D"],
          ["AT&T", "NYSE:T|1D"],
          ["Verizon", "NYSE:VZ|1D"],
        ],
      },
    ],
  },
  {
    slug: "health-care",
    eyebrow: "HEALTH CARE",
    title: "医疗保健：药物、器械与服务",
    description:
      "从 XLV 到生物科技、医疗器械，再观察药企、保险和生命科学工具。",
    groups: [
      {
        heading: "板块与子行业代理",
        description: "XLV 是医疗锚；IBB、XBI 与 IHI 区分生物科技和医疗器械。",
        symbols: [
          ["医疗保健 XLV", "AMEX:XLV|1D"],
          ["生物科技 IBB", "NASDAQ:IBB|1D"],
          ["生物科技等权 XBI", "AMEX:XBI|1D"],
          ["医疗器械 IHI", "AMEX:IHI|1D"],
        ],
      },
      {
        heading: "核心公司",
        description: "覆盖大型药企、管理式医疗、医疗器械和生命科学工具。",
        symbols: [
          ["Eli Lilly", "NYSE:LLY|1D"],
          ["UnitedHealth", "NYSE:UNH|1D"],
          ["Johnson & Johnson", "NYSE:JNJ|1D"],
          ["AbbVie", "NYSE:ABBV|1D"],
          ["Thermo Fisher", "NYSE:TMO|1D"],
          ["Intuitive Surgical", "NASDAQ:ISRG|1D"],
        ],
      },
    ],
  },
  {
    slug: "industrials",
    eyebrow: "INDUSTRIALS",
    title: "工业：资本开支与运输",
    description: "把综合工业、国防航空、基建与运输放进同一张周期地图。",
    groups: [
      {
        heading: "板块与子行业代理",
        description:
          "XLI 是工业锚；ITA、PAVE 与 IYT 分别观察国防、基建和运输。",
        symbols: [
          ["工业 XLI", "AMEX:XLI|1D"],
          ["国防航空 ITA", "CBOE:ITA|1D"],
          ["美国基建 PAVE", "CBOE:PAVE|1D"],
          ["运输 IYT", "CBOE:IYT|1D"],
        ],
      },
      {
        heading: "核心公司",
        description: "覆盖航空发动机、机械、国防、铁路、电气化和运输平台。",
        symbols: [
          ["GE Aerospace", "NYSE:GE|1D"],
          ["Caterpillar", "NYSE:CAT|1D"],
          ["RTX", "NYSE:RTX|1D"],
          ["Union Pacific", "NYSE:UNP|1D"],
          ["Eaton", "NYSE:ETN|1D"],
          ["Uber", "NYSE:UBER|1D"],
        ],
      },
    ],
  },
  {
    slug: "energy",
    eyebrow: "ENERGY",
    title: "能源：油价、服务与管道",
    description: "用综合能源、油服、勘探生产和中游四条线观察能源周期。",
    groups: [
      {
        heading: "板块与子行业代理",
        description: "XLE 是能源锚；OIH、XOP 与 AMLP 补充油服、上游和中游。",
        symbols: [
          ["能源 XLE", "AMEX:XLE|1D"],
          ["油服 OIH", "NASDAQ:OIH|1D"],
          ["勘探生产 XOP", "AMEX:XOP|1D"],
          ["中游 AMLP", "AMEX:AMLP|1D"],
        ],
      },
      {
        heading: "核心公司",
        description: "覆盖综合石油、独立上游、油服和天然气基础设施。",
        symbols: [
          ["Exxon Mobil", "NYSE:XOM|1D"],
          ["Chevron", "NYSE:CVX|1D"],
          ["ConocoPhillips", "NYSE:COP|1D"],
          ["SLB", "NYSE:SLB|1D"],
          ["EOG Resources", "NYSE:EOG|1D"],
          ["Williams", "NYSE:WMB|1D"],
        ],
      },
    ],
  },
  {
    slug: "materials",
    eyebrow: "MATERIALS",
    title: "原材料：化工、金属与矿业",
    description: "从综合原材料拆到黄金、铜、锂和主要材料公司。",
    groups: [
      {
        heading: "板块与主题代理",
        description:
          "XLB 是综合锚；GDX、COPX 与 LIT 分别观察黄金、铜和锂产业链。",
        symbols: [
          ["原材料 XLB", "AMEX:XLB|1D"],
          ["黄金矿业 GDX", "AMEX:GDX|1D"],
          ["铜矿 COPX", "AMEX:COPX|1D"],
          ["锂电材料 LIT", "AMEX:LIT|1D"],
        ],
      },
      {
        heading: "核心公司",
        description: "覆盖工业气体、涂料、铜、黄金、钢铁和基础化工。",
        symbols: [
          ["Linde", "NASDAQ:LIN|1D"],
          ["Sherwin-Williams", "NYSE:SHW|1D"],
          ["Freeport-McMoRan", "NYSE:FCX|1D"],
          ["Newmont", "NYSE:NEM|1D"],
          ["Nucor", "NYSE:NUE|1D"],
          ["Dow", "NYSE:DOW|1D"],
        ],
      },
    ],
  },
  {
    slug: "real-estate",
    eyebrow: "REAL ESTATE",
    title: "房地产：利率敏感资产",
    description: "用 REIT ETF 与物流、数据中心、医疗和零售地产观察利率传导。",
    groups: [
      {
        heading: "板块与子行业代理",
        description: "XLRE、VNQ 与 SCHH 是权益 REIT 代理；REM 观察抵押 REIT。",
        symbols: [
          ["房地产 XLRE", "AMEX:XLRE|1D"],
          ["Vanguard REIT VNQ", "AMEX:VNQ|1D"],
          ["Schwab REIT SCHH", "AMEX:SCHH|1D"],
          ["抵押 REIT REM", "CBOE:REM|1D"],
        ],
      },
      {
        heading: "核心公司",
        description: "覆盖物流、通信塔、数据中心、医疗、购物中心和净租赁。",
        symbols: [
          ["Prologis", "NYSE:PLD|1D"],
          ["American Tower", "NYSE:AMT|1D"],
          ["Equinix", "NASDAQ:EQIX|1D"],
          ["Welltower", "NYSE:WELL|1D"],
          ["Simon Property", "NYSE:SPG|1D"],
          ["Realty Income", "NYSE:O|1D"],
        ],
      },
    ],
  },
  {
    slug: "utilities",
    eyebrow: "UTILITIES",
    title: "公用事业：防守、电网与电力",
    description: "观察传统公用事业、防守属性，以及数据中心带来的电力需求主题。",
    groups: [
      {
        heading: "板块与主题代理",
        description:
          "XLU 是公用事业锚；VPU、IDU 与 NLR 提供综合和核电主题对照。",
        symbols: [
          ["公用事业 XLU", "AMEX:XLU|1D"],
          ["Vanguard 公用事业 VPU", "AMEX:VPU|1D"],
          ["iShares 公用事业 IDU", "AMEX:IDU|1D"],
          ["核能 NLR", "AMEX:NLR|1D"],
        ],
      },
      {
        heading: "核心公司",
        description: "覆盖受监管公用事业、核电运营商和独立电力生产商。",
        symbols: [
          ["NextEra Energy", "NYSE:NEE|1D"],
          ["Southern Company", "NYSE:SO|1D"],
          ["Constellation Energy", "NASDAQ:CEG|1D"],
          ["Duke Energy", "NYSE:DUK|1D"],
          ["Vistra", "NYSE:VST|1D"],
          ["American Electric Power", "NASDAQ:AEP|1D"],
        ],
      },
    ],
  },
  {
    slug: "luxury",
    eyebrow: "LUXURY",
    title: "奢侈品：定价权与周期",
    description:
      "观察 LVMH、爱马仕与法拉利的长期分化，同时明确跨币种比较的限制。",
    groups: [
      {
        heading: "三家公司",
        description:
          "MC 与 RMS 以欧元交易，RACE 以美元交易；这里只比较价格路径，不合成指数。",
        symbols: [
          ["LVMH", "EURONEXT:MC|1D"],
          ["Hermès", "EURONEXT:RMS|1D"],
          ["Ferrari", "NYSE:RACE|1D"],
        ],
      },
    ],
  },
] as const satisfies readonly MarketTheme[];
