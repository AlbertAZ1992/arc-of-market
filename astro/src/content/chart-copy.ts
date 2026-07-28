import { chartIndex } from "@/content/chart-index";
import type { ChartIndexEntry } from "@/content/types";
import type { ArcChartKind, ArcChartSpec } from "@/lib/arc-chart-types";

type DefaultChartCopy = {
  description: string;
  interpretation: readonly string[];
  whatToWatch: readonly string[];
};

const defaultCopy: Record<ArcChartKind, DefaultChartCopy> = {
  annual: {
    description: "按自然年汇总回报，未结束年份只代表当前年内结果。",
    interpretation: [
      "年度结果经常偏离长期平均值，平均数不能代表一个典型年份。",
    ],
    whatToWatch: ["比较上涨年份占比、极端亏损年份和连续亏损是否集中出现。"],
  },
  changes: {
    description: "按日期列出指数成分的新增与剔除。",
    interpretation: [
      "指数会持续替换不再具有代表性的公司，成分名单不是静态组合。",
    ],
    whatToWatch: ["区分公司基本面变化和指数委员会的代表性调整。"],
  },
  cycles: {
    description: "按阶段划分高点、低点、持续时间和累计涨跌幅。",
    interpretation: [
      "牛市通常持续更久，熊市通常下跌更快，但每轮幅度差异很大。",
    ],
    whatToWatch: ["周期划分依赖确认后的高低点，不用于实时预测转折日期。"],
  },
  distribution: {
    description: "把历史回报放入固定区间，观察常见结果与尾部结果。",
    interpretation: ["极端年份少见，却会对长期复利产生不成比例的影响。"],
    whatToWatch: ["同时看样本数量和区间边界，不只看平均值。"],
  },
  drawdown: {
    description: "从每个历史高点计算下跌深度、持续时间和修复过程。",
    interpretation: ["相同跌幅可能对应完全不同的下跌速度和回本时间。"],
    whatToWatch: ["当前回撤只有在重新创出高点后，才能确认完整修复时间。"],
  },
  drivers: {
    description: "把总回报拆成不同来源，比较每部分的年度贡献。",
    interpretation: ["单年贡献可能很小，长期再投资会放大累计差距。"],
    whatToWatch: ["核对价格回报、现金分配和再投资使用的口径。"],
  },
  extremes: {
    description: "并列历史最佳与最差单日回报，观察尾部事件幅度。",
    interpretation: ["最大的上涨日和下跌日经常出现在同一段高波动时期。"],
    whatToWatch: ["极端日说明尾部风险存在，不代表同样幅度会按固定频率重演。"],
  },
  holding: {
    description: "比较不同持有年限的胜率、中位回报和有效样本数量。",
    interpretation: ["历史上持有期越长，负回报样本越少，但可用样本也会下降。"],
    whatToWatch: ["长持有期样本高度重叠，不能当成彼此独立的试验。"],
  },
  intrayear: {
    description: "对照每年最大年内回撤与同一年的最终回报。",
    interpretation: ["年中明显回撤与年末正回报可以同时发生。"],
    whatToWatch: ["未结束年份的最终回报仍会变化，不与完整历史年份直接下结论。"],
  },
  multiline: {
    description: "把相关指标放在同一时间轴，比较方向、幅度和背离。",
    interpretation: ["重点看指标是否同步变化，以及背离持续了多长时间。"],
    whatToWatch: ["先核对每条线的单位、频率和数据起点。"],
  },
  nested: {
    description: "比较同一数据组内的多条时间序列。",
    interpretation: ["相对位置和变化方向通常比单个绝对值更有解释力。"],
    whatToWatch: ["不同序列可能使用不同单位或右轴，阅读前先核对图例。"],
  },
  price: {
    description: "使用完整价格历史观察长期趋势、阶段高点和修复时间。",
    interpretation: ["累计结果不显示中途最大损失，需与同页回撤图一起读取。"],
    whatToWatch: ["跨越数量级的长期图使用对数坐标，避免早期变化被压缩。"],
  },
  rolling: {
    description: "从每个起点计算固定持有期的年化回报。",
    interpretation: ["起点估值和所处周期会明显改变随后数年的持有结果。"],
    whatToWatch: ["相邻滚动窗口高度重叠，不能视为独立样本。"],
  },
  rollmatrix: {
    description: "在同一时间轴比较五年、十年和二十年等持有期结果。",
    interpretation: ["持有期拉长通常压缩结果分布，但不会消除起点差异。"],
    whatToWatch: ["长持有期越接近当前，可用完整窗口越少。"],
  },
  seasonality: {
    description: "比较各月份平均回报、上涨概率和样本数量。",
    interpretation: ["季节性是历史频率，不是单独的交易信号。"],
    whatToWatch: ["平均回报可能被少数极端年份拉动，要同时看上涨概率。"],
  },
  snapshot: {
    description: "展示最近一期的截面数据和相对位置。",
    interpretation: ["快照说明当前差异，不说明差异会持续多久。"],
    whatToWatch: ["核对快照日期、覆盖范围和缺失样本。"],
  },
  valuation: {
    description: "把当前估值或风险价格放回自己的历史区间。",
    interpretation: ["历史位置说明市场定价有多高或多低，不给出精确转折时间。"],
    whatToWatch: ["价格与盈利变化都能改变估值，必须区分是哪一项在移动。"],
  },
  volatility: {
    description: "比较短期与中期实现波动率，观察价格变化速度。",
    interpretation: ["波动率衡量变化幅度，不直接表示上涨或下跌方向。"],
    whatToWatch: ["高波动持续时间和期限结构比单日尖峰更重要。"],
  },
};

export type ChartKey = keyof typeof chartIndex;

export function resolveChartSpec(chart: ChartKey): ArcChartSpec {
  const entry: ChartIndexEntry = chartIndex[chart];
  const fallback = defaultCopy[entry.kind];
  return {
    ...entry,
    description: entry.description ?? fallback.description,
    id: chart,
    interpretation: entry.interpretation ?? fallback.interpretation,
    whatToWatch: entry.whatToWatch ?? fallback.whatToWatch,
  };
}
