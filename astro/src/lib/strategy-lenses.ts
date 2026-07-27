export const strategyLenses = [
  {
    cadence: "日频",
    code: "ARC TREND",
    description: "把价格相对中长期趋势的位置，整理成扩张、观望与防守三种环境。",
    dimension: "主要趋势",
    title: "趋势引擎",
  },
  {
    cadence: "日频 / 周频",
    code: "ARC PULSE",
    description:
      "同时观察趋势强度、市场参与和波动变化，判断上涨或下跌是否得到确认。",
    dimension: "市场强弱",
    title: "市场脉冲",
  },
  {
    cadence: "周频",
    code: "ARC BALANCE",
    description: "比较成长与价值的相对力量，观察市场偏好正在向哪一侧倾斜。",
    dimension: "风格迁移",
    title: "风格天平",
  },
  {
    cadence: "月频",
    code: "ARC CLOCK",
    description: "把产业投资、资本开支与市场表现放回更长的创新周期中理解。",
    dimension: "长期周期",
    title: "创新时钟",
  },
] as const;
