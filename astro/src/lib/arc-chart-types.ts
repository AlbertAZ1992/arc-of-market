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
  id: string;
  kind: ArcChartKind;
  scaleType?: "linear" | "log";
  source: string;
  series?: readonly {
    axis?: number;
    key: string;
    label: string;
    unit?: string;
    valueKey?: string;
  }[];
  title: string;
  valueKey?: string;
  valueLabel?: string;
  yUnit?: string;
};
