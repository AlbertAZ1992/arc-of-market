import { BarChart, LineChart, ScatterChart } from "echarts/charts";
import {
  AriaComponent,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import type { EChartsCoreOption } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

import type { ArcChartKind } from "@/lib/arc-chart-types";
import { ARC_ECHARTS_THEME, ARC_ECHARTS_THEME_DARK } from "@/lib/echarts-theme";

type JsonRecord = Record<string, unknown>;
type Row = Record<string, string | number | boolean | null>;

echarts.use([
  AriaComponent,
  BarChart,
  CanvasRenderer,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  LineChart,
  ScatterChart,
  TooltipComponent,
]);
echarts.registerTheme("arc", ARC_ECHARTS_THEME);
echarts.registerTheme("arc-dark", ARC_ECHARTS_THEME_DARK);

const positive = "#00a487";
const negative = "#f60c3e";
const neutral = "#272727";

function record(value: unknown): JsonRecord {
  return typeof value === "object" && value !== null
    ? (value as JsonRecord)
    : {};
}

function strings(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

function numbers(value: unknown): Array<number | null> {
  if (!Array.isArray(value)) return [];
  return value.map((item) => (typeof item === "number" ? item : null));
}

function rows(value: unknown): Row[] {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (item): item is Row => typeof item === "object" && item !== null,
  );
}

function axisOption(unit = ""): EChartsCoreOption {
  return {
    animation: false,
    aria: { enabled: true },
    grid: { bottom: 52, containLabel: true, left: 12, right: 18, top: 52 },
    tooltip: { trigger: "axis" },
    xAxis: {
      axisLabel: { hideOverlap: true },
      boundaryGap: false,
      type: "category",
    },
    yAxis: { name: unit, scale: true, type: "value" },
  };
}

function priceOption(
  data: JsonRecord,
  unit: string,
  scaleType: "linear" | "log",
): EChartsCoreOption {
  return {
    ...axisOption(unit),
    xAxis: { data: strings(data["dates"]), type: "category" },
    yAxis: {
      name: unit,
      scale: true,
      type: scaleType === "log" ? "log" : "value",
    },
    series: [
      {
        areaStyle: { color: "rgba(246, 12, 62, 0.08)" },
        data: numbers(data["close"]),
        lineStyle: { color: negative, width: 1.5 },
        name: "指数",
        sampling: "lttb",
        showSymbol: false,
        type: "line",
      },
    ],
  };
}

function annualOption(data: JsonRecord): EChartsCoreOption {
  const returns = numbers(data["returns"]);
  return {
    ...axisOption("%"),
    xAxis: { data: strings(data["years"]), type: "category" },
    series: [
      {
        data: returns.map((value) => ({
          itemStyle: { color: (value ?? 0) >= 0 ? positive : negative },
          value,
        })),
        name: "年度回报",
        type: "bar",
      },
    ],
  };
}

function distributionOption(data: JsonRecord): EChartsCoreOption {
  const buckets = rows(data["buckets"]);
  return {
    ...axisOption("年份数"),
    xAxis: {
      axisLabel: { interval: 0, rotate: 25 },
      data: buckets.map((item) => String(item["label"] ?? "")),
      type: "category",
    },
    series: [
      {
        data: buckets.map((item) => Number(item["count"] ?? 0)),
        itemStyle: { color: negative },
        name: "年份数",
        type: "bar",
      },
    ],
  };
}

function holdingOption(data: JsonRecord): EChartsCoreOption {
  const values = rows(data["rows"]);
  return {
    ...axisOption("%"),
    legend: { data: ["胜率", "中位年化回报"] },
    xAxis: {
      data: values.map((item) => `${item["years"] ?? ""} 年`),
      type: "category",
    },
    series: [
      {
        data: values.map((item) => Number(item["win"] ?? 0)),
        name: "胜率",
        type: "bar",
      },
      {
        data: values.map((item) => Number(item["median"] ?? 0)),
        name: "中位年化回报",
        type: "line",
      },
    ],
  };
}

function lineOption(
  data: JsonRecord,
  key: string,
  label: string,
  unit: string,
  scaleType: "linear" | "log" = "linear",
): EChartsCoreOption {
  return {
    ...axisOption(unit),
    xAxis: { data: strings(data["dates"]), type: "category" },
    yAxis: {
      name: unit,
      scale: true,
      type: scaleType === "log" ? "log" : "value",
    },
    series: [
      {
        areaStyle:
          key === "dd" ? { color: "rgba(246, 12, 62, 0.12)" } : undefined,
        data: numbers(data[key]),
        lineStyle: { color: key === "dd" ? negative : neutral, width: 1.4 },
        name: label,
        sampling: "lttb",
        showSymbol: false,
        type: "line",
      },
    ],
  };
}

function volatilityOption(data: JsonRecord): EChartsCoreOption {
  const candidates = [
    ["20 日实现波动", "vol20"],
    ["60 日实现波动", "vol60"],
    [String(data["vol_index_name"] ?? "波动率指数"), "vol_index"],
  ] as const;
  const series = candidates.filter(([, key]) => numbers(data[key]).length > 0);
  return {
    ...axisOption("%"),
    legend: { data: series.map(([label]) => label) },
    xAxis: { data: strings(data["dates"]), type: "category" },
    series: series.map(([name, key]) => ({
      data: numbers(data[key]),
      name,
      sampling: "lttb",
      showSymbol: false,
      type: "line",
    })),
  };
}

function nestedOption(
  data: JsonRecord,
  element: HTMLElement,
): EChartsCoreOption {
  const raw = element.dataset["series"] ?? "[]";
  const specs = JSON.parse(raw) as Array<{
    axis?: number;
    key: string;
    label: string;
    unit?: string;
    valueKey?: string;
  }>;
  const hasSecondAxis = specs.some((spec) => spec.axis === 1);
  return {
    ...axisOption(specs[0]?.unit ?? ""),
    legend: { data: specs.map((spec) => spec.label) },
    xAxis: { type: "time" },
    yAxis: hasSecondAxis
      ? [
          {
            name: specs.find((spec) => spec.axis !== 1)?.unit ?? "",
            type: "value",
          },
          {
            name: specs.find((spec) => spec.axis === 1)?.unit ?? "",
            position: "right",
            type: "value",
          },
        ]
      : { name: specs[0]?.unit ?? "", type: "value" },
    series: specs.map((spec) => {
      const nested = record(data[spec.key]);
      const dates = strings(nested["dates"]);
      const values = numbers(nested[spec.valueKey ?? "values"]);
      return {
        data: dates.map((date, index) => [date, values[index] ?? null]),
        name: spec.label,
        sampling: "lttb",
        showSymbol: false,
        type: "line",
        yAxisIndex: spec.axis ?? 0,
      };
    }),
  };
}

function multilineOption(
  data: JsonRecord,
  element: HTMLElement,
): EChartsCoreOption {
  const specs = JSON.parse(element.dataset["series"] ?? "[]") as Array<{
    axis?: number;
    key: string;
    label: string;
    unit?: string;
  }>;
  const dates = strings(data["dates"]);
  const hasSecondAxis = specs.some((spec) => spec.axis === 1);
  return {
    ...axisOption(specs[0]?.unit ?? ""),
    legend: { data: specs.map((spec) => spec.label) },
    xAxis: { data: dates, type: "category" },
    yAxis: hasSecondAxis
      ? [
          {
            name: specs.find((spec) => spec.axis !== 1)?.unit ?? "",
            type: "value",
          },
          {
            name: specs.find((spec) => spec.axis === 1)?.unit ?? "",
            position: "right",
            type: "value",
          },
        ]
      : { name: specs[0]?.unit ?? "", scale: true, type: "value" },
    series: specs.map((spec) => ({
      data: numbers(data[spec.key]),
      name: spec.label,
      sampling: "lttb",
      showSymbol: dates.length <= 24,
      type: "line",
      yAxisIndex: spec.axis ?? 0,
    })),
  };
}

function snapshotOption(
  data: JsonRecord,
  element: HTMLElement,
): EChartsCoreOption {
  const specs = JSON.parse(element.dataset["series"] ?? "[]") as Array<{
    key: string;
    label: string;
    unit?: string;
  }>;
  const latest = record(data["latest"]);
  return {
    ...axisOption(specs[0]?.unit ?? ""),
    xAxis: { data: specs.map((spec) => spec.label), type: "category" },
    series: [
      {
        data: specs.map((spec) => Number(latest[spec.key] ?? 0)),
        itemStyle: { color: negative },
        label: { formatter: "{c}", position: "top", show: true },
        name: "最新值",
        type: "bar",
      },
    ],
  };
}

function intrayearOption(data: JsonRecord): EChartsCoreOption {
  const values = rows(data["rows"]);
  return {
    ...axisOption("%"),
    tooltip: {
      formatter: (params: { data?: [number, number, number] }) => {
        const point = params.data ?? [0, 0, 0];
        return `${point[2]} 年<br/>年内最大跌幅 ${point[0]}%<br/>全年 ${point[1]}%`;
      },
      trigger: "item",
    },
    xAxis: { name: "年内最大跌幅 %", scale: true, type: "value" },
    yAxis: { name: "年度回报 %", scale: true, type: "value" },
    series: [
      {
        data: values.map((item) => [
          Number(item["intra_dd"] ?? 0),
          Number(item["ret"] ?? 0),
          Number(item["year"] ?? 0),
        ]),
        itemStyle: { color: negative },
        name: "年份",
        symbolSize: 7,
        type: "scatter",
      },
    ],
  };
}

function cyclesOption(data: JsonRecord): EChartsCoreOption {
  const values = rows(data["cycles"]).slice(-36);
  return {
    ...axisOption("%"),
    xAxis: {
      axisLabel: { rotate: 30 },
      data: values.map((item) => String(item["start"] ?? "").slice(0, 7)),
      type: "category",
    },
    series: [
      {
        data: values.map((item) => ({
          itemStyle: {
            color: item["kind"] === "bull" ? positive : negative,
          },
          value: Number(item["ret"] ?? 0),
        })),
        name: "牛熊周期回报",
        type: "bar",
      },
    ],
  };
}

function changesOption(data: JsonRecord): EChartsCoreOption {
  const counts = new Map<string, number>();
  for (const item of rows(data["changes"])) {
    const year = String(item["effective_date"] ?? "").slice(0, 4);
    if (!year) continue;
    counts.set(year, (counts.get(year) ?? 0) + 1);
  }
  const values = Array.from(counts.entries()).sort(([left], [right]) =>
    left.localeCompare(right),
  );
  return {
    ...axisOption("事件数"),
    xAxis: {
      axisLabel: { hideOverlap: true },
      data: values.map(([year]) => year),
      type: "category",
    },
    series: [
      {
        data: values.map(([, count]) => count),
        itemStyle: { color: negative },
        name: "成分变更事件",
        type: "bar",
      },
    ],
  };
}

function seasonalityOption(data: JsonRecord): EChartsCoreOption {
  const values = rows(data["rows"]);
  return {
    ...axisOption("%"),
    legend: { data: ["平均回报", "上涨概率"] },
    xAxis: {
      data: values.map((item) => `${item["month"] ?? ""} 月`),
      type: "category",
    },
    yAxis: [
      { name: "平均回报 %", type: "value" },
      {
        max: 100,
        min: 0,
        name: "上涨概率 %",
        position: "right",
        type: "value",
      },
    ],
    series: [
      {
        data: values.map((item) => Number(item["avg"] ?? 0)),
        name: "平均回报",
        type: "bar",
      },
      {
        data: values.map((item) => Number(item["win"] ?? 0)),
        name: "上涨概率",
        type: "line",
        yAxisIndex: 1,
      },
    ],
  };
}

function driversOption(data: JsonRecord): EChartsCoreOption {
  const values = rows(data["rows"]);
  return {
    ...axisOption("%"),
    legend: { data: ["盈利贡献", "估值贡献", "年度回报"] },
    xAxis: {
      data: values.map((item) => String(item["year"] ?? "")),
      type: "category",
    },
    series: [
      {
        data: values.map((item) => Number(item["r_eps"] ?? 0)),
        name: "盈利贡献",
        stack: "driver",
        type: "bar",
      },
      {
        data: values.map((item) => Number(item["r_valuation"] ?? 0)),
        name: "估值贡献",
        stack: "driver",
        type: "bar",
      },
      {
        data: values.map((item) => Number(item["r_total"] ?? 0)),
        name: "年度回报",
        showSymbol: false,
        type: "line",
      },
    ],
  };
}

function rollmatrixOption(data: JsonRecord): EChartsCoreOption {
  const series = [
    ["5 年", "cagr5"],
    ["10 年", "cagr10"],
    ["20 年", "cagr20"],
  ] as const;
  return {
    ...axisOption("年化 %"),
    legend: { data: series.map(([label]) => label) },
    xAxis: { data: strings(data["dates"]), type: "category" },
    series: series.map(([name, key]) => ({
      data: numbers(data[key]),
      name,
      sampling: "lttb",
      showSymbol: false,
      type: "line",
    })),
  };
}

function extremesOption(data: JsonRecord): EChartsCoreOption {
  const values = [
    ...rows(data["worst"]).slice(0, 8).reverse(),
    ...rows(data["best"]).slice(0, 8),
  ];
  return {
    ...axisOption("%"),
    grid: { bottom: 32, containLabel: true, left: 8, right: 30, top: 18 },
    xAxis: { type: "value" },
    yAxis: {
      data: values.map((item) => String(item["date"] ?? "")),
      type: "category",
    },
    series: [
      {
        data: values.map((item) => {
          const value = Number(item["ret"] ?? 0);
          return {
            itemStyle: { color: value >= 0 ? positive : negative },
            value,
          };
        }),
        name: "单日回报",
        type: "bar",
      },
    ],
  };
}

function optionFor(
  kind: ArcChartKind,
  data: JsonRecord,
  element: HTMLElement,
): EChartsCoreOption {
  const key = element.dataset["valueKey"] ?? "values";
  const label = element.dataset["valueLabel"] ?? "数值";
  const unit = element.dataset["yUnit"] ?? "";
  const scaleType = element.dataset["scaleType"] === "log" ? "log" : "linear";
  const options: Record<ArcChartKind, () => EChartsCoreOption> = {
    annual: () => annualOption(data),
    changes: () => changesOption(data),
    cycles: () => cyclesOption(data),
    distribution: () => distributionOption(data),
    drawdown: () => lineOption(data, "dd", "回撤", "%"),
    drivers: () => driversOption(data),
    extremes: () => extremesOption(data),
    holding: () => holdingOption(data),
    intrayear: () => intrayearOption(data),
    multiline: () => multilineOption(data, element),
    nested: () => nestedOption(data, element),
    price: () => priceOption(data, unit, scaleType),
    rolling: () => lineOption(data, "cagr", "五年年化回报", "%"),
    rollmatrix: () => rollmatrixOption(data),
    seasonality: () => seasonalityOption(data),
    snapshot: () => snapshotOption(data, element),
    valuation: () => lineOption(data, key, label, unit, scaleType),
    volatility: () => volatilityOption(data),
  };
  return options[kind]();
}

async function renderChart(element: HTMLElement): Promise<void> {
  const path = element.dataset["dataPath"];
  const kind = element.dataset["kind"] as ArcChartKind | undefined;
  if (!path || !kind) throw new Error("图表配置不完整");
  const response = await fetch(path);
  if (!response.ok) throw new Error("本批数据尚未生成");
  const data = record(await response.json());
  const option = optionFor(kind, data, element);
  element.querySelector("[data-chart-status]")?.remove();
  const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const chart = echarts.init(element, dark ? "arc-dark" : "arc");
  chart.setOption(option);
  element.dataset["arcChartReady"] = "rendered";
  new ResizeObserver(() => chart.resize()).observe(element);
}

function queueChart(element: HTMLElement): void {
  if (element.dataset["arcChartReady"]) return;
  element.dataset["arcChartReady"] = "queued";
  const observer = new IntersectionObserver(
    (entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return;
      observer.disconnect();
      renderChart(element).catch((error: unknown) => {
        const status = element.querySelector("[data-chart-status]");
        if (status) status.textContent = `数据暂不可用：${String(error)}`;
        element.dataset["arcChartReady"] = "error";
      });
    },
    { rootMargin: "360px 0px" },
  );
  observer.observe(element);
}

export function bootArcJsonCharts(): void {
  document
    .querySelectorAll<HTMLElement>("[data-arc-json-chart]")
    .forEach(queueChart);
}
