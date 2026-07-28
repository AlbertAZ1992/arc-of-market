export const strategyLenses = [
  {
    cadence: "日频",
    code: "ARC TREND",
    description: "比较价格与中长期趋势线，计划输出扩张、观望或防守三种状态。",
    dimension: "主要趋势",
    title: "趋势引擎",
  },
  {
    cadence: "日频 / 周频",
    code: "ARC PULSE",
    description:
      "同时比较趋势强度、上涨成分比例和波动率，计划判断涨跌是否得到多数股票确认。",
    dimension: "市场强弱",
    title: "市场脉冲",
  },
  {
    cadence: "周频",
    code: "ARC BALANCE",
    description: "比较成长股与价值股的相对回报，计划识别当前领先的市场风格。",
    dimension: "风格迁移",
    title: "风格天平",
  },
  {
    cadence: "月频",
    code: "ARC CLOCK",
    description:
      "比较产业投资、资本开支和相关股票表现，计划判断技术投资所处阶段。",
    dimension: "长期周期",
    title: "创新时钟",
  },
] as const;
