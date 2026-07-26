export type ThemeResearchEntry = {
  description: string;
  id: string;
  source: string;
  title: string;
};

export const themeResearch: Record<string, readonly ThemeResearchEntry[]> = {
  semiconductors: [
    {
      id: "semiconductor-annual",
      title: "半导体年度涨跌",
      description: "按自然年比较半导体板块代理的回报分布。",
      source: "SMH、SOXX 历史价格",
    },
    {
      id: "semiconductor-intrayear",
      title: "年内最大跌幅",
      description: "比较每年年内最大回撤与年末回报。",
      source: "SMH、SOXX 历史价格",
    },
    {
      id: "semiconductor-weights",
      title: "SMH 与 SOXX 权重差异",
      description: "按同一观察日期比较两只 ETF 的主要持仓权重。",
      source: "VanEck 与 iShares 官方持仓文件",
    },
  ],
  "information-technology": [
    {
      id: "xlk-annual",
      title: "XLK 年度涨跌",
      description: "科技板块 ETF 的年度回报与极端年份。",
      source: "XLK 历史价格",
    },
    {
      id: "xlk-intrayear",
      title: "XLK 年内最大跌幅",
      description: "比较科技板块每年的年内最大回撤与年度结果。",
      source: "XLK 历史价格",
    },
    {
      id: "xlk-holdings",
      title: "XLK 头部持仓",
      description: "展示头部公司权重与累计集中度。",
      source: "State Street 官方持仓文件",
    },
  ],
  financials: [
    {
      id: "xlf-annual",
      title: "金融板块年度涨跌",
      description: "金融板块 ETF 的年度回报与极端年份。",
      source: "XLF 历史价格",
    },
    {
      id: "xlf-yield-curve",
      title: "收益率曲线 × XLF",
      description: "在同一时间轴比较 10Y−2Y 利差与金融板块回报。",
      source: "FRED 与 XLF 历史价格",
    },
    {
      id: "xlf-holdings",
      title: "XLF 头部持仓",
      description: "展示金融板块主要公司权重与累计集中度。",
      source: "State Street 官方持仓文件",
    },
  ],
  consumer: [
    {
      id: "consumer-annual",
      title: "消费板块年度回报",
      description: "比较必需消费与可选消费的年度分化。",
      source: "XLP 与 XLY 历史价格",
    },
    {
      id: "consumer-equal-weight",
      title: "等权组合回报",
      description: "用固定再平衡规则计算消费龙头等权组合。",
      source: "消费龙头历史价格 · ArcOfMarket 计算",
    },
    {
      id: "consumer-drawdowns",
      title: "消费龙头回撤",
      description: "比较消费龙头历史回撤深度与修复时长。",
      source: "消费龙头历史价格 · ArcOfMarket 计算",
    },
  ],
};
