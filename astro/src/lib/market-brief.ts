import etfProxies from "../../public/data/etf_proxies.json";
import equityAllocation from "../../public/data/equity_allocation.json";
import financialStress from "../../public/data/financial_stress.json";
import mag7EqualWeight from "../../public/data/mag7_equal_weight.json";
import mag7Weight from "../../public/data/mag7_weight.json";
import macroRates from "../../public/data/macro_rates.json";
import ndxBreadth from "../../public/data/ndx_breadth.json";
import sp500Drawdowns from "../../public/data/sp500_drawdowns.json";
import sp500Breadth from "../../public/data/sp500_breadth.json";
import sp500Intrayear from "../../public/data/sp500_intrayear.json";
import volFamily from "../../public/data/vol_family.json";

type NumberSeries = {
  dates: string[];
  values: number[];
};

type ProxyData = {
  dates: string[];
  series: Record<"DIA" | "QQQ" | "SPY", { values: number[] }>;
};

type BreadthData = {
  dates: string[];
  latest_200ma: number;
  latest_50ma: number;
  pct_above_50ma: number[];
};

type StressData = {
  latest: {
    date: string;
    fsi: number;
  };
  series: {
    fsi: NumberSeries;
  } & Record<string, NumberSeries>;
};

type VolatilityData = {
  VIX: {
    close: number[];
    dates: string[];
  };
  VIX3M: {
    close: number[];
    dates: string[];
  };
};

type ConcentrationData = {
  meta: {
    latest_date: string;
    latest_weight_pct: number;
  };
};

type AllocationData = NumberSeries & {
  meta: {
    as_of: string;
    current_percentile: number;
  };
};

type YieldSeries = NumberSeries;

type YieldCurveData = {
  t10y2y: YieldSeries;
};

type IntrayearData = {
  rows: Array<{
    intra_dd: number;
    partial_year?: boolean;
    ret: number;
    year: number;
  }>;
};

type DrawdownData = {
  dd: number[];
};

export type NarrativeSection = {
  body: string;
  headline: string;
  takeaway: string;
};

export type MarketEvidence = {
  detail: string;
  icon: "graph-up-linear" | "shield-check-linear" | "stars-linear";
  label: string;
  state: string;
  tone: "calm" | "caution" | "positive";
};

export type MarketBrief = {
  asOf: string;
  breadth: {
    ndx50: number;
    sp50050: number;
  };
  concentration: number;
  evidence: MarketEvidence[];
  evidenceTitle: string;
  headline: string;
  marketReturns: Record<"DIA" | "MAG7" | "QQQ" | "SPY", number>;
  narrative: {
    allocation: NarrativeSection;
    breadth: NarrativeSection;
    hero: string;
    history: NarrativeSection;
    risk: NarrativeSection;
  };
  sourceDates: {
    breadth: string;
    concentration: string;
    price: string;
    stress: string;
    volatility: string;
  };
  stress: number;
  summary: string;
  vix: number;
  vixCurve: number;
};

export const MARKET_BRIEF_THRESHOLDS = {
  breadthHealthy: 60,
  stressAverage: 0,
  vixCaution: 22,
} as const;

function latestValue(values: number[]): number {
  return values.at(-1) ?? 0;
}

function periodReturn(values: number[], periods = 20): number {
  const current = latestValue(values);
  const start = values.at(-(periods + 1)) ?? values.at(0) ?? current;
  return start === 0 ? 0 : (current / start - 1) * 100;
}

function formatPercent(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

function formatPoint(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}`;
}

function describeMove(label: string, value: number): string {
  return `${label} ${value >= 0 ? "上涨" : "下跌"} ${Math.abs(value).toFixed(1)}%`;
}

function percentile(values: number[], current: number): number {
  if (values.length === 0) return 0;
  return (values.filter((value) => value <= current).length / values.length) * 100;
}

function average(values: number[]): number {
  return values.length === 0
    ? 0
    : values.reduce((total, value) => total + value, 0) / values.length;
}

function lastPositiveCross(series: YieldSeries): string | undefined {
  let crossing: string | undefined;
  for (let index = 1; index < series.values.length; index += 1) {
    const previous = series.values[index - 1];
    const current = series.values[index];
    if (previous !== undefined && current !== undefined && previous <= 0 && current > 0) {
      crossing = series.dates[index];
    }
  }
  return crossing;
}

function buildHeadline(
  returns: MarketBrief["marketReturns"],
  sp500Breadth: number,
  ndxBreadth: number,
): Pick<MarketBrief, "evidenceTitle" | "headline" | "summary"> {
  const dowLeads = returns.DIA >= returns.QQQ;
  const leadLabel = dowLeads ? "道指" : "QQQ";
  const lagLabel = dowLeads ? "QQQ" : "道指";
  const leadReturn = dowLeads ? returns.DIA : returns.QQQ;
  const lagReturn = dowLeads ? returns.QQQ : returns.DIA;
  const spread = Math.abs(returns.DIA - returns.QQQ);
  const breadthGap = sp500Breadth - ndxBreadth;
  const breadthReading =
    breadthGap >= 10
      ? `标普的上涨参与面比纳指宽 ${breadthGap.toFixed(1)} 个百分点`
      : breadthGap <= -10
        ? `纳指的上涨参与面比标普宽 ${Math.abs(breadthGap).toFixed(1)} 个百分点`
        : "标普与纳指的短期参与面接近";
  return {
    evidenceTitle:
      `${leadLabel} 与 ${lagLabel} 的 20 日回报已经拉开 ` +
      `${spread.toFixed(1)} 个百分点`,
    headline:
      `${leadLabel} ${formatPercent(leadReturn)}，${lagLabel} ` +
      `${formatPercent(lagReturn)}：过去 20 日，` +
      `${dowLeads ? "蓝筹相对科技" : "科技相对蓝筹"}领先 ` +
      `${spread.toFixed(1)} 个百分点。`,
    summary:
      `同期 SPY ${formatPercent(returns.SPY)}，七巨头等权篮子 ` +
      `${formatPercent(returns.MAG7)}；${breadthReading}。`,
  };
}

function buildNarrative(
  returns: MarketBrief["marketReturns"],
  spBreadth: BreadthData,
  nasdaqBreadth: BreadthData,
  volatility: VolatilityData,
  stressData: StressData,
): MarketBrief["narrative"] {
  const allocation = equityAllocation as AllocationData;
  const rates = macroRates as YieldCurveData;
  const intrayear = sp500Intrayear as IntrayearData;
  const drawdowns = sp500Drawdowns as DrawdownData;
  const vix = latestValue(volatility.VIX.close);
  const vix3m = latestValue(volatility.VIX3M.close);
  const stress = stressData.latest.fsi;
  const currentYear = intrayear.rows.at(-1);
  const allocationValue = latestValue(allocation.values) * 100;
  const spreadValue = latestValue(rates.t10y2y.values);
  const crossingDate = lastPositiveCross(rates.t10y2y);
  const spPercentile = percentile(spBreadth.pct_above_50ma, spBreadth.latest_50ma);
  const ndxPercentile = percentile(
    nasdaqBreadth.pct_above_50ma,
    nasdaqBreadth.latest_50ma,
  );
  const averageIntrayear = average(intrayear.rows.map((row) => row.intra_dd));
  const currentDrawdown = latestValue(drawdowns.dd);
  const breadthGap = spBreadth.latest_50ma - nasdaqBreadth.latest_50ma;
  const breadthLeader = breadthGap >= 0 ? "标普" : "纳指";
  const breadthLaggard = breadthGap >= 0 ? "纳指" : "标普";
  const riskElevated =
    vix >= MARKET_BRIEF_THRESHOLDS.vixCaution ||
    stress > MARKET_BRIEF_THRESHOLDS.stressAverage;
  const riskTakeaway =
    returns.QQQ < 0
      ? riskElevated
        ? "科技股回撤已经得到波动率或金融压力的确认，" +
          "需要继续检查压力是否扩散。"
        : "科技股回撤尚未得到期权期限结构和金融系统压力的共同确认；" +
          "这不等于科技股已经见底。"
      : riskElevated
        ? "科技股上涨与较高风险定价同时出现，" +
          "价格强势没有消除金融条件压力。"
        : "科技股上涨没有伴随风险指标恶化，" +
          "但低压力本身不保证涨势延续。";
  return {
    hero:
      `SPY 同期 ${formatPercent(returns.SPY)}，标普 50 日广度为 ` +
      `${spBreadth.latest_50ma.toFixed(1)}%；七巨头等权篮子 ` +
      `${formatPercent(returns.MAG7)}，纳指 100 广度只有 ` +
      `${nasdaqBreadth.latest_50ma.toFixed(1)}%。指数没有一起涨，也没有一起跌。`,
    breadth: {
      headline:
        `标普有 ${spBreadth.latest_50ma.toFixed(1)}% 的成分站上 50 日线，` +
        `纳指只有 ${nasdaqBreadth.latest_50ma.toFixed(1)}%。`,
      body:
        `${breadthLeader}领先${breadthLaggard} ${Math.abs(breadthGap).toFixed(1)} ` +
        `个百分点。标普读数高于 2022 年 5 月以来约 ${spPercentile.toFixed(0)}% ` +
        `的观测日，纳指读数只高于约 ${ndxPercentile.toFixed(0)}%。`,
      takeaway:
        breadthGap >= 0
          ? `标普的短期上涨覆盖面更广；纳指 200 日广度仍有 ` +
            `${nasdaqBreadth.latest_200ma.toFixed(1)}%，` +
            "说明当前先转弱的是短期参与度。"
          : `纳指的短期上涨覆盖面更广；标普 200 日广度为 ` +
            `${spBreadth.latest_200ma.toFixed(1)}%，需要继续核对中期参与度。`,
    },
    risk: {
      headline:
        `${describeMove("QQQ", returns.QQQ)}，` +
        `${returns.QQQ < 0 ? "但" : "同时"} VIX 与金融压力` +
        `${riskElevated ? "已经" : "没有同步"}进入警戒区。`,
      body:
        `VIX 为 ${vix.toFixed(1)}，处于 1990 年以来约第 ` +
        `${percentile(volatility.VIX.close, vix).toFixed(0)} 百分位；` +
        `VIX3M 比现货高 ${(vix3m - vix).toFixed(1)} 点。OFR FSI 为 ` +
        `${stress.toFixed(2)}，处于 2000 年以来约第 ` +
        `${percentile(stressData.series.fsi.values, stress).toFixed(0)} 百分位。`,
      takeaway: riskTakeaway,
    },
    allocation: {
      headline:
        `股票配置占比为 ${allocationValue.toFixed(1)}%，` +
        `10 年减 2 年美债利差为 ${formatPoint(spreadValue)} 个百分点。`,
      body:
        `股票配置高于 1945 年以来 ${allocation.meta.current_percentile.toFixed(1)}% ` +
        `的季度观测；收益率曲线最近一次由非正转为正值是在 ` +
        `${crossingDate ?? "—"}。`,
      takeaway:
        "高股票配置压缩长期回报的安全垫；" +
        "曲线重新转正描述融资环境变化，不单独构成衰退或买卖信号。",
    },
    history: {
      headline:
        `${currentYear?.year ?? "本年"} 年内一度回撤 ` +
        `${formatPercent(currentYear?.intra_dd ?? 0)}，截至数据日回报 ` +
        `${formatPercent(currentYear?.ret ?? 0)}。`,
      body:
        `1928 年以来，年内最大回撤平均为 ${formatPercent(averageIntrayear)}；` +
        `当前指数距历史高点 ${formatPercent(currentDrawdown)}。`,
      takeaway:
        "年中出现回撤是常态，年内最深跌幅不能直接决定全年结果；" +
        "需要同时看修复速度和市场广度。",
    },
  };
}

export function loadMarketBrief(): MarketBrief {
  const proxies = etfProxies as ProxyData;
  const mag7 = mag7EqualWeight as NumberSeries;
  const spBreadth = sp500Breadth as BreadthData;
  const nasdaqBreadth = ndxBreadth as BreadthData;
  const stressData = financialStress as StressData;
  const volatility = volFamily as VolatilityData;
  const concentration = mag7Weight as ConcentrationData;
  const returns = {
    DIA: periodReturn(proxies.series.DIA.values),
    MAG7: periodReturn(mag7.values),
    QQQ: periodReturn(proxies.series.QQQ.values),
    SPY: periodReturn(proxies.series.SPY.values),
  };
  const positiveMarkets = Object.values(returns).filter(
    (value) => value > 0,
  ).length;
  const breadthHealthy =
    spBreadth.latest_50ma >= MARKET_BRIEF_THRESHOLDS.breadthHealthy &&
    nasdaqBreadth.latest_50ma >= 50;
  const breadthSplit =
    Math.abs(spBreadth.latest_50ma - nasdaqBreadth.latest_50ma) >= 15;
  const stress = stressData.latest.fsi;
  const vix = latestValue(volatility.VIX.close);
  const vix3m = latestValue(volatility.VIX3M.close);
  const riskElevated =
    stress > MARKET_BRIEF_THRESHOLDS.stressAverage ||
    vix >= MARKET_BRIEF_THRESHOLDS.vixCaution;
  const headline = buildHeadline(
    returns,
    spBreadth.latest_50ma,
    nasdaqBreadth.latest_50ma,
  );
  const narrative = buildNarrative(
    returns,
    spBreadth,
    nasdaqBreadth,
    volatility,
    stressData,
  );
  const priceDate = proxies.dates.at(-1) ?? stressData.latest.date;
  const breadthDate = spBreadth.dates.at(-1) ?? priceDate;
  const concentrationValue = concentration.meta.latest_weight_pct;

  return {
    asOf: priceDate,
    breadth: {
      ndx50: nasdaqBreadth.latest_50ma,
      sp50050: spBreadth.latest_50ma,
    },
    concentration: concentrationValue,
    evidence: [
      {
        detail:
          `20D · SPY ${formatPercent(returns.SPY)} · QQQ ${formatPercent(returns.QQQ)} · ` +
          `DIA ${formatPercent(returns.DIA)} · Mag7 ${formatPercent(returns.MAG7)}`,
        icon: "graph-up-linear",
        label: "趋势",
        state: `${positiveMarkets}/4 上涨`,
        tone: positiveMarkets >= 3 ? "positive" : "caution",
      },
      {
        detail:
          `>50MA · S&P ${spBreadth.latest_50ma.toFixed(1)}% · ` +
          `NDX ${nasdaqBreadth.latest_50ma.toFixed(1)}% · Mag7 权重 ` +
          `${concentrationValue.toFixed(1)}%`,
        icon: "stars-linear",
        label: "广度",
        state: breadthSplit
          ? "标普强于纳指"
          : breadthHealthy
            ? "参与度扩散"
            : "内部仍分化",
        tone: breadthHealthy && !breadthSplit ? "positive" : "caution",
      },
      {
        detail:
          `VIX ${vix.toFixed(1)} · 3M−现货 ${formatPoint(vix3m - vix)}` +
          ` · OFR FSI ${stress.toFixed(2)}`,
        icon: "shield-check-linear",
        label: "风险",
        state: riskElevated ? "风险升温" : "压力低于均值",
        tone: riskElevated ? "caution" : "calm",
      },
    ],
    evidenceTitle: headline.evidenceTitle,
    headline: headline.headline,
    marketReturns: returns,
    narrative,
    sourceDates: {
      breadth: breadthDate,
      concentration: concentration.meta.latest_date,
      price: priceDate,
      stress: stressData.latest.date,
      volatility: volatility.VIX.dates.at(-1) ?? priceDate,
    },
    stress,
    summary: headline.summary,
    vix,
    vixCurve: vix3m - vix,
  };
}
