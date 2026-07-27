import financialStress from "../../public/data/financial_stress.json";
import sp500Century from "../../public/data/sp500_century.json";
import volFamily from "../../public/data/vol_family.json";

type PriceSeries = {
  close: number[];
  dates: string[];
};

type StressData = {
  latest: {
    date: string;
    fsi: number;
  };
};

type VolatilitySeries = {
  close: number[];
  dates: string[];
};

type VolatilityData = {
  VIX: VolatilitySeries;
  VIX3M: VolatilitySeries;
};

export const MARKET_BRIEF_THRESHOLDS = {
  longTrendDays: 200,
  stressAverage: 0,
  vixCaution: 22,
} as const;

export type MarketEvidence = {
  detail: string;
  icon: "graph-up-linear" | "shield-check-linear" | "stars-linear";
  label: string;
  state: string;
  tone: "calm" | "caution" | "positive";
};

export type MarketBrief = {
  asOf: string;
  evidence: MarketEvidence[];
  evidenceTitle: string;
  headline: string;
  sourceDates: {
    price: string;
    stress: string;
    volatility: string;
  };
  summary: string;
  vix: number;
};

function average(values: number[]): number {
  return values.reduce((total, value) => total + value, 0) / values.length;
}

function latestValue(values: number[]): number {
  return values.at(-1) ?? 0;
}

function formatPercent(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

function describeHeadline(
  aboveLongTrend: boolean,
  stress: number,
  vix: number,
): Pick<MarketBrief, "evidenceTitle" | "headline" | "summary"> {
  if (!aboveLongTrend) {
    return {
      evidenceTitle: "标普 500：价格跌破长期趋势，风险控制优先",
      headline: "长期趋势已经转弱，风险预算需要收缩。",
      summary:
        "价格跌破长期趋势线，当前重点是等待风险压力回落，而不是提前猜测反转。",
    };
  }
  if (
    stress > MARKET_BRIEF_THRESHOLDS.stressAverage ||
    vix >= MARKET_BRIEF_THRESHOLDS.vixCaution
  ) {
    return {
      evidenceTitle: "标普 500：趋势仍在，压力指标开始升温",
      headline: "长期趋势仍在，但风险定价正在升温。",
      summary:
        "价格结构尚未破坏，波动或金融压力却已经抬头，需要降低追涨速度并观察确认。",
    };
  }
  return {
    evidenceTitle: "标普 500：趋势仍在，波动率尚未确认系统性风险",
    headline: "趋势仍然向上，系统性压力暂未升温。",
    summary:
      "价格保持在长期趋势线上方，金融压力低于历史均值；当前更适合持续观察，而不是追逐短期涨幅。",
  };
}

export function loadMarketBrief(): MarketBrief {
  const prices = sp500Century as PriceSeries;
  const stressData = financialStress as StressData;
  const volatility = volFamily as VolatilityData;
  const close = latestValue(prices.close);
  const average20 = average(prices.close.slice(-20));
  const average200 = average(
    prices.close.slice(-MARKET_BRIEF_THRESHOLDS.longTrendDays),
  );
  const gap20 = (close / average20 - 1) * 100;
  const gap200 = (close / average200 - 1) * 100;
  const stress = stressData.latest.fsi;
  const vix = latestValue(volatility.VIX.close);
  const vix3m = latestValue(volatility.VIX3M.close);
  const headline = describeHeadline(close > average200, stress, vix);
  const priceDate = prices.dates.at(-1) ?? stressData.latest.date;
  const volatilityDate = volatility.VIX.dates.at(-1) ?? stressData.latest.date;

  return {
    asOf: priceDate,
    ...headline,
    sourceDates: {
      price: priceDate,
      stress: stressData.latest.date,
      volatility: volatilityDate,
    },
    vix,
    evidence: [
      {
        detail:
          `S&P 500 · 20D ${formatPercent(gap20)} · ` +
          `200D ${formatPercent(gap200)}`,
        icon: "graph-up-linear",
        label: "趋势",
        state: close > average200 ? "仍然向上" : "转为防守",
        tone: close > average200 ? "positive" : "caution",
      },
      {
        detail: `OFR FSI ${stress.toFixed(2)} · 历史均值为 0`,
        icon: "stars-linear",
        label: "压力",
        state:
          stress <= MARKET_BRIEF_THRESHOLDS.stressAverage
            ? "低于均值"
            : "高于均值",
        tone:
          stress <= MARKET_BRIEF_THRESHOLDS.stressAverage ? "calm" : "caution",
      },
      {
        detail:
          `VIX ${vix.toFixed(1)} · 3M − 现货 ` +
          `${vix3m >= vix ? "+" : ""}${(vix3m - vix).toFixed(1)}`,
        icon: "shield-check-linear",
        label: "风险",
        state:
          vix < MARKET_BRIEF_THRESHOLDS.vixCaution ? "尚未确认" : "正在升温",
        tone: vix < MARKET_BRIEF_THRESHOLDS.vixCaution ? "calm" : "caution",
      },
    ],
  };
}
