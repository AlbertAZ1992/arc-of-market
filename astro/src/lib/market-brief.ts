import etfProxies from "../../public/data/etf_proxies.json";
import financialStress from "../../public/data/financial_stress.json";
import mag7EqualWeight from "../../public/data/mag7_equal_weight.json";
import mag7Weight from "../../public/data/mag7_weight.json";
import ndxBreadth from "../../public/data/ndx_breadth.json";
import sp500Breadth from "../../public/data/sp500_breadth.json";
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
};

type StressData = {
  latest: {
    date: string;
    fsi: number;
  };
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

function buildHeadline(
  positiveMarkets: number,
  sp500Breadth: number,
  ndxBreadth: number,
  vix: number,
  stress: number,
): Pick<MarketBrief, "evidenceTitle" | "headline" | "summary"> {
  return {
    evidenceTitle: "SPY、QQQ、DIA 与七巨头过去 20 个交易日回报",
    headline:
      `过去 20 个交易日：${positiveMarkets}/4 类市场上涨；` +
      `标普 50 日广度 ${sp500Breadth.toFixed(1)}%，` +
      `纳指 100 为 ${ndxBreadth.toFixed(1)}%。`,
    summary:
      `VIX 为 ${vix.toFixed(1)}，${
        vix >= MARKET_BRIEF_THRESHOLDS.vixCaution ? "高于" : "低于"
      } ${MARKET_BRIEF_THRESHOLDS.vixCaution} 的警戒线；` +
      `OFR FSI 为 ${stress.toFixed(2)}，${
        stress > MARKET_BRIEF_THRESHOLDS.stressAverage ? "高于" : "低于"
      }历史均值。`,
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
    positiveMarkets,
    spBreadth.latest_50ma,
    nasdaqBreadth.latest_50ma,
    vix,
    stress,
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
