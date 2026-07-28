export type ArcChartKind =
  | "annual"
  | "changes"
  | "cycles"
  | "distribution"
  | "drawdown"
  | "drivers"
  | "extremes"
  | "holding"
  | "intrayear"
  | "multiline"
  | "nested"
  | "price"
  | "rolling"
  | "rollmatrix"
  | "seasonality"
  | "snapshot"
  | "valuation"
  | "volatility";

export type ArcChartSpec = {
  dataPath: string;
  description: string;
  eyebrow?: string | undefined;
  id: string;
  interpretation?: readonly string[] | undefined;
  kind: ArcChartKind;
  note?: string | undefined;
  scaleType?: "linear" | "log" | undefined;
  source: string;
  series?: readonly {
    axis?: number | undefined;
    key: string;
    label: string;
    unit?: string | undefined;
    valueKey?: string | undefined;
  }[] | undefined;
  title: string;
  valueKey?: string | undefined;
  valueLabel?: string | undefined;
  whatToWatch?: readonly string[] | undefined;
  yUnit?: string | undefined;
};
