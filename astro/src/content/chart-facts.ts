import type { ArcChartSpec } from "@/lib/arc-chart-types";

type JsonMap = Record<string, unknown>;
type Summarizer = (data: JsonMap, spec: ArcChartSpec) => string[];

const publicData = import.meta.glob<JsonMap>("../../public/data/*.json", {
  eager: true,
  import: "default",
});

function asMap(value: unknown): JsonMap | undefined {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as JsonMap)
    : undefined;
}

function asMaps(value: unknown): JsonMap[] {
  return Array.isArray(value)
    ? value.map(asMap).filter((item) => item !== undefined)
    : [];
}

function asNumbers(value: unknown): number[] {
  return Array.isArray(value)
    ? value.filter((item): item is number => Number.isFinite(item))
    : [];
}

function asLabels(value: unknown): Array<number | string> {
  return Array.isArray(value)
    ? value.filter(
        (item): item is number | string =>
          typeof item === "string" || Number.isFinite(item),
      )
    : [];
}

function numberValue(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

function textValue(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function formatNumber(value: number, digits = 1): string {
  return value.toLocaleString("zh-CN", { maximumFractionDigits: digits });
}

function formatPercent(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumber(value)}%`;
}

function pairedValues(
  labels: Array<number | string>,
  values: number[],
): Array<{ label: number | string; value: number }> {
  return values.flatMap((value, index) => {
    const label = labels[index];
    return label === undefined ? [] : [{ label, value }];
  });
}

function average(values: number[]): number {
  return values.length === 0
    ? 0
    : values.reduce((total, value) => total + value, 0) / values.length;
}

function percentile(values: number[], current: number): number {
  if (values.length === 0) return 0;
  return (values.filter((value) => value <= current).length / values.length) * 100;
}

function elapsedYears(start: number | string, end: number | string): number {
  const startDate = new Date(`${start}T00:00:00Z`);
  const endDate = new Date(`${end}T00:00:00Z`);
  const milliseconds = endDate.getTime() - startDate.getTime();
  return milliseconds / (365.2425 * 24 * 60 * 60 * 1000);
}

function summarizeAnnual(data: JsonMap): string[] {
  const pairs = pairedValues(
    asLabels(data["years"]),
    asNumbers(data["returns"]),
  );
  const latest = pairs.at(-1);
  if (!latest || pairs.length === 0) return [];
  const best = pairs.reduce((left, right) =>
    right.value > left.value ? right : left,
  );
  const worst = pairs.reduce((left, right) =>
    right.value < left.value ? right : left,
  );
  const partial = String(data["partial_year"]) === String(latest.label);
  const asOf = textValue(data["as_of"]);
  const completed = partial ? pairs.slice(0, -1) : pairs;
  const positiveYears = completed.filter((pair) => pair.value > 0).length;
  const negativeYears = completed.filter((pair) => pair.value < 0).length;
  const flatYears = completed.length - positiveYears - negativeYears;
  const latestLabel =
    partial && asOf
      ? `截至 ${asOf}，${latest.label} 年内回报`
      : `${latest.label} 年回报`;
  return [
    `${completed.length} 个完整年度里，${positiveYears} 年上涨、` +
      `${negativeYears} 年下跌${flatYears > 0 ? `、${flatYears} 年持平` : ""}。` +
      `${latestLabel}为 ${formatPercent(latest.value)}；` +
      `样本最好年份为 ${best.label} 年 ${formatPercent(best.value)}，` +
      `最差为 ${worst.label} 年 ${formatPercent(worst.value)}。`,
  ];
}

function summarizePrice(data: JsonMap): string[] {
  const dates = asLabels(data["dates"]);
  const values =
    asNumbers(data["close"]).length > 0
      ? asNumbers(data["close"])
      : asNumbers(data["values"]);
  const pairs = pairedValues(dates, values);
  const first = pairs.at(0);
  const latest = pairs.at(-1);
  if (!first || !latest || first.value === 0)
    return summarizeTickerPrices(data);
  const multiple = latest.value / first.value;
  const years = elapsedYears(first.label, latest.label);
  const annualized = years > 0 && multiple > 0
    ? (multiple ** (1 / years) - 1) * 100
    : 0;
  return [
    `${first.label} 至 ${latest.label}，序列由 ${formatNumber(first.value)} ` +
      `变为 ${formatNumber(latest.value)}，相当于起点的 ` +
      `${formatNumber(multiple)} 倍，年化复合约 ${formatPercent(annualized)}。`,
  ];
}

function summarizeTickerPrices(data: JsonMap): string[] {
  const tickers = asMap(data["tickers"]);
  const latestDate = asLabels(data["dates"]).at(-1);
  if (!tickers || latestDate === undefined) return [];
  const changes = Object.entries(tickers)
    .flatMap(([ticker, raw]) => {
      const values = asNumbers(asMap(raw)?.["values"]);
      const first = values.at(0);
      const latest = values.at(-1);
      return first && latest
        ? [{ ticker, value: (latest / first - 1) * 100 }]
        : [];
    })
    .sort((left, right) => right.value - left.value);
  const best = changes.at(0);
  const worst = changes.at(-1);
  const bestText = best
    ? `${best.ticker} ${formatPercent(best.value)}`
    : "";
  const worstText = worst
    ? `${worst.ticker} ${formatPercent(worst.value)}`
    : "";
  return best && worst
    ? [
        `截至 ${latestDate}，累计回报最高为 ${bestText}，最低为 ${worstText}。`,
      ]
    : [];
}

function summarizeCycles(data: JsonMap): string[] {
  const cycles = asMaps(data["cycles"]);
  const latest = cycles.at(-1);
  if (!latest) return [];
  const kind = latest["kind"] === "bull" ? "牛市" : "熊市";
  const bearCycles = cycles.filter((cycle) => cycle["kind"] === "bear");
  const deepestBear = bearCycles.reduce<JsonMap | undefined>(
    (deepest, cycle) =>
      !deepest ||
      (numberValue(cycle["ret"]) ?? 0) < (numberValue(deepest["ret"]) ?? 0)
        ? cycle
        : deepest,
    undefined,
  );
  const start = latest["start"];
  const end = textValue(latest["end"]);
  const period = end ? `${start} 至 ${end}` : `${start} 开始，当前仍在进行`;
  return [
    `最近一轮标记为${kind}：${period}，` +
      `累计回报 ${formatPercent(numberValue(latest["ret"]) ?? 0)}，` +
      `持续 ${formatNumber(numberValue(latest["days"]) ?? 0, 0)} 天。` +
      (deepestBear
        ? `样本最深熊市从 ${deepestBear["start"]} 开始，` +
          `累计下跌 ${formatPercent(numberValue(deepestBear["ret"]) ?? 0)}。`
        : ""),
  ];
}

function summarizeExtremes(data: JsonMap): string[] {
  const best = asMaps(data["best"]).at(0);
  const worst = asMaps(data["worst"]).at(0);
  if (!best || !worst) return [];
  const bestReturn = formatPercent(numberValue(best["ret"]) ?? 0);
  const worstReturn = formatPercent(numberValue(worst["ret"]) ?? 0);
  return [
    `样本共 ${formatNumber(numberValue(data["days_total"]) ?? 0, 0)} 个交易日；` +
      `最大单日上涨为 ${best["date"]} 的 ${bestReturn}，` +
      `最大单日下跌为 ${worst["date"]} 的 ${worstReturn}。`,
  ];
}

function summarizeDistribution(data: JsonMap): string[] {
  const buckets = asMaps(data["buckets"]);
  if (buckets.length === 0) return [];
  const common = buckets.reduce((left, right) =>
    (numberValue(right["count"]) ?? 0) > (numberValue(left["count"]) ?? 0)
      ? right
      : left,
  );
  return [
    `${formatNumber(numberValue(data["years_total"]) ?? 0, 0)} 个年度中，` +
      `出现最多的回报区间是 ${common["label"]}，共 ` +
      `${formatNumber(numberValue(common["count"]) ?? 0, 0)} 年。`,
  ];
}

function summarizeHolding(data: JsonMap): string[] {
  const rows = asMaps(data["rows"]);
  const oneYear = rows.find((row) => numberValue(row["years"]) === 1);
  const fiveYears = rows.find((row) => numberValue(row["years"]) === 5);
  const twentyYears =
    rows.find((row) => numberValue(row["years"]) === 20) ?? rows.at(-1);
  if (!oneYear || !fiveYears || !twentyYears) return [];
  return [
    `一年持有期的历史正回报比例为 ` +
      `${formatNumber(numberValue(oneYear["win"]) ?? 0)}%，五年提高到 ` +
      `${formatNumber(numberValue(fiveYears["win"]) ?? 0)}%，` +
      `${twentyYears["years"]} 年为 ` +
      `${formatNumber(numberValue(twentyYears["win"]) ?? 0)}%。` +
      `时间降低了历史亏损概率，但没有把它降到零。`,
  ];
}

function summarizeRolling(data: JsonMap): string[] {
  const dates = asLabels(data["dates"]);
  const values = asNumbers(data["cagr"]);
  const pairs = pairedValues(dates, values);
  const latest = pairs.at(-1);
  if (!latest || pairs.length === 0) return [];
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  return [
    `截至 ${latest.label} 的滚动年化回报为 ${formatPercent(latest.value)}；` +
      `历史区间为 ${formatPercent(minimum)} 至 ${formatPercent(maximum)}。`,
  ];
}

function summarizeRollMatrix(data: JsonMap): string[] {
  const date = asLabels(data["dates"]).at(-1);
  if (date === undefined) return [];
  const values = [
    ["5 年", asNumbers(data["cagr5"]).at(-1)],
    ["10 年", asNumbers(data["cagr10"]).at(-1)],
    ["20 年", asNumbers(data["cagr20"]).at(-1)],
  ].filter((item): item is [string, number] => item[1] !== undefined);
  return values.length > 0
    ? [
        `截至 ${date}：${values
          .map(([label, value]) => `${label}年化 ${formatPercent(value)}`)
          .join("；")}。`,
      ]
    : [];
}

function summarizeIntrayear(data: JsonMap): string[] {
  const rows = asMaps(data["rows"]);
  const latest = rows.at(-1);
  if (!latest) return [];
  const averageDrawdown = average(
    rows.flatMap((row) => {
      const value = numberValue(row["intra_dd"]);
      return value === undefined ? [] : [value];
    }),
  );
  return [
    `${latest["year"]} 年内最大回撤为 ` +
      `${formatPercent(numberValue(latest["intra_dd"]) ?? 0)}，` +
      `截至数据日的年度回报为 ${formatPercent(numberValue(latest["ret"]) ?? 0)}。` +
      `样本内年均最深回撤为 ${formatPercent(averageDrawdown)}；` +
      `年中下跌并不直接决定年末涨跌。`,
  ];
}

function summarizeSeasonality(data: JsonMap): string[] {
  const rows = asMaps(data["rows"]);
  if (rows.length === 0) return [];
  const best = rows.reduce((left, right) =>
    (numberValue(right["avg"]) ?? 0) > (numberValue(left["avg"]) ?? 0)
      ? right
      : left,
  );
  const worst = rows.reduce((left, right) =>
    (numberValue(right["avg"]) ?? 0) < (numberValue(left["avg"]) ?? 0)
      ? right
      : left,
  );
  return [
    `${data["years"]} 样本中，${best["month"]} 月平均回报最高，` +
      `为 ${formatPercent(numberValue(best["avg"]) ?? 0)}；` +
      `${worst["month"]} 月最低，为 ${formatPercent(numberValue(worst["avg"]) ?? 0)}。`,
  ];
}

function summarizeDrawdown(data: JsonMap): string[] {
  const dates = asLabels(data["dates"]);
  const current = pairedValues(dates, asNumbers(data["dd"])).at(-1);
  const episodes = asMaps(data["episodes"]);
  if (!current || episodes.length === 0) return [];
  const worst = episodes.reduce((left, right) =>
    (numberValue(right["depth"]) ?? 0) < (numberValue(left["depth"]) ?? 0)
      ? right
      : left,
  );
  return [
    `${current.label} 的当前回撤为 ${formatPercent(current.value)}；` +
      `样本最深回撤为 ${worst["peak"]} 高点后 ` +
      `${formatPercent(numberValue(worst["depth"]) ?? 0)}，谷底在 ` +
      `${worst["trough"]}，直到 ${worst["recovery"]} 才收复前高。`,
  ];
}

function summarizeVolatility(data: JsonMap): string[] {
  const date = asLabels(data["dates"]).at(-1);
  const vol20 = asNumbers(data["vol20"]).at(-1);
  const vol60 = asNumbers(data["vol60"]).at(-1);
  if (date === undefined || vol20 === undefined || vol60 === undefined)
    return [];
  const percentile20 = percentile(asNumbers(data["vol20"]), vol20);
  return [
    `截至 ${date}，20 日年化实现波动率为 ${formatNumber(vol20)}%，` +
      `处于样本约第 ${formatNumber(percentile20, 0)} 百分位；` +
      `60 日为 ${formatNumber(vol60)}%。`,
  ];
}

function summarizeDrivers(data: JsonMap): string[] {
  const year = asLabels(data["years"]).at(-1);
  const price = asNumbers(data["price_return"]).at(-1);
  const total = asNumbers(data["total_return"]).at(-1);
  const dividend = asNumbers(data["dividend_contribution"]).at(-1);
  if (
    year === undefined ||
    price === undefined ||
    total === undefined ||
    dividend === undefined
  ) {
    return [];
  }
  const dividendPoints = formatNumber(dividend);
  return [
    `截至数据日，${year} 年价格回报为 ${formatPercent(price)}，总回报为 ` +
      `${formatPercent(total)}，股息及再投资贡献为 ${dividendPoints} 个百分点。`,
  ];
}

function findSeriesData(data: JsonMap, key: string): JsonMap | undefined {
  return asMap(data[key]) ?? asMap(asMap(data["series"])?.[key]);
}

function summarizeSeries(data: JsonMap, spec: ArcChartSpec): string[] {
  const breadth50 = numberValue(data["latest_50ma"]);
  const breadth200 = numberValue(data["latest_200ma"]);
  const breadthDate = asLabels(data["dates"]).at(-1);
  if (
    breadth50 !== undefined &&
    breadth200 !== undefined &&
    breadthDate !== undefined
  ) {
    const breadth50Values = asNumbers(data["pct_above_50ma"]);
    const breadth200Values = asNumbers(data["pct_above_200ma"]);
    return [
      `截至 ${breadthDate}，高于 50 日均线的成分占 ${formatNumber(breadth50)}%，` +
        `位于样本约第 ${formatNumber(percentile(breadth50Values, breadth50), 0)} ` +
        `百分位；高于 200 日均线的成分占 ${formatNumber(breadth200)}%，` +
        `位于约第 ${formatNumber(percentile(breadth200Values, breadth200), 0)} 百分位。`,
    ];
  }
  const facts =
    spec.series?.flatMap((series) => {
      const nested = findSeriesData(data, series.key);
      const values =
        asNumbers(nested?.[series.valueKey ?? "values"]).length > 0
          ? asNumbers(nested?.[series.valueKey ?? "values"])
          : asNumbers(data[series.key]);
      const dates =
        asLabels(nested?.["dates"]).length > 0
          ? asLabels(nested?.["dates"])
          : asLabels(data["dates"]);
      const value = values.at(-1);
      const date = dates.at(-1);
      return value === undefined || date === undefined
        ? []
        : [
            {
              date: String(date),
              label: series.label,
              percentile: percentile(values, value),
              unit: series.unit ?? "",
              value,
            },
          ];
    }) ?? [];
  if (facts.length === 0) return summarizeNamedValuation(data);
  const latestDate = facts
    .map((fact) => fact.date)
    .sort()
    .at(-1);
  if (facts.length === 1) {
    const fact = facts[0];
    return fact
      ? [
          `截至 ${latestDate}，${fact.label}为 ${formatNumber(fact.value)}` +
            `${fact.unit ? ` ${fact.unit}` : ""}，位于样本约第 ` +
            `${formatNumber(fact.percentile, 0)} 百分位。`,
        ]
      : [];
  }
  return [
    `截至 ${latestDate}：${facts
      .slice(0, 4)
      .map(
        (fact) =>
          `${fact.label} ${formatNumber(fact.value)}${fact.unit ? ` ${fact.unit}` : ""}`,
      )
      .join("；")}。`,
  ];
}

function summarizeNamedValuation(data: JsonMap): string[] {
  const names = ["nvda", "csco"];
  const facts = names.flatMap((name) => {
    const series = asMap(data[name]);
    const date = asLabels(series?.["dates"]).at(-1);
    const value = asNumbers(series?.["trailing_pe"]).at(-1);
    return date === undefined || value === undefined
      ? []
      : [{ date, name: name.toUpperCase(), value }];
  });
  return facts.length > 0
    ? [
        `截至 ${facts[0]?.date}：${facts
          .map((fact) => `${fact.name} TTM PE ${formatNumber(fact.value)} 倍`)
          .join("；")}。`,
      ]
    : [];
}

function summarizeValuation(data: JsonMap, spec: ArcChartSpec): string[] {
  if (spec.valueLabel === "总回报指数") {
    return summarizePrice(data);
  }
  const values = asNumbers(data[spec.valueKey ?? "values"]);
  const dates = asLabels(data["dates"]);
  const latest = pairedValues(dates, values).at(-1);
  return latest
    ? [
        `截至 ${latest.label}，${spec.valueLabel ?? spec.title}为 ` +
          `${formatNumber(latest.value)}${spec.yUnit ? ` ${spec.yUnit}` : ""}，` +
          `位于样本约第 ${formatNumber(percentile(values, latest.value), 0)} 百分位。`,
      ]
    : summarizeSeries(data, spec);
}

function summarizeChanges(data: JsonMap): string[] {
  const changes = asMaps(data["changes"]);
  const latest = changes.at(0);
  if (!latest) return [];
  const addition = asMap(latest["addition"]);
  const removal = asMap(latest["removal"]);
  const names = [
    textValue(addition?.["ticker"])
      ? `调入 ${addition?.["ticker"]}`
      : undefined,
    textValue(removal?.["ticker"]) ? `剔除 ${removal?.["ticker"]}` : undefined,
  ].filter((item) => item !== undefined);
  const changeText = names.length > 0 ? `，${names.join("、")}` : "";
  return [
    `共记录 ${formatNumber(changes.length, 0)} 次成分调整；` +
      `最近生效日为 ${latest["effective_date"]}${changeText}。`,
  ];
}

const summarizers: Partial<Record<ArcChartSpec["kind"], Summarizer>> = {
  annual: summarizeAnnual,
  changes: summarizeChanges,
  cycles: summarizeCycles,
  distribution: summarizeDistribution,
  drawdown: summarizeDrawdown,
  drivers: summarizeDrivers,
  extremes: summarizeExtremes,
  holding: summarizeHolding,
  intrayear: summarizeIntrayear,
  multiline: summarizeSeries,
  nested: summarizeSeries,
  price: summarizePrice,
  rolling: summarizeRolling,
  rollmatrix: summarizeRollMatrix,
  seasonality: summarizeSeasonality,
  valuation: summarizeValuation,
  volatility: summarizeVolatility,
};

export function loadChartFacts(spec: ArcChartSpec): string[] {
  const summarize = summarizers[spec.kind];
  if (!summarize || !spec.dataPath) return [];
  const key = `../../public${spec.dataPath}`;
  const data = publicData[key];
  return data ? summarize(data, spec) : [];
}
