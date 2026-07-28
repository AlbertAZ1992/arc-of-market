import type { ArcChartKind } from "@/lib/arc-chart-types";

// ─── Block types ───

/** A chart block — references a chart definition from the chart index. */
export type ChartBlock = {
  type: "chart";
  /** Key into ChartIndex */
  chart: string;
};

/** A prose block managed by the page-content JSON. */
export type ProseBlock = {
  content: string;
  type: "prose";
};

/** A custom component block — rendered by a named Astro component. */
export type ComponentBlock = {
  type: "component";
  /** Component identifier: "Sp500Composition" | "ConstituentChanges" | "MacroDashboard" etc. */
  component: string;
};

export type Block = ChartBlock | ProseBlock | ComponentBlock;

// ─── Chapter / Section ───

export type ChapterSpec = {
  /** DOM anchor id */
  id: string;
  /** Sidebar nav label (short) */
  navLabel: string;
  /** Chapter heading label, e.g. "§ I · THE SHAPE OF RETURNS" */
  label: string;
  /** Chapter title, e.g. "回报的形状" */
  title: string;
  /** Optional intro prose key */
  intro?: string;
  /** Optional "how to read" / guide prose key */
  guide?: string;
  /** Blocks in order */
  blocks: Block[];
};

// ─── Page schema ───

export type PageSchema = {
  route: string;
  seo: {
    title: string;
    description: string;
  };
  hero: {
    eyebrow: string;
    headline: string;
    intro: string;
  };
  chapters: ChapterSpec[];
};

// ─── Chart index entry ───

export type ChartIndexEntry = {
  /** Default title — can be overridden in prose */
  title: string;
  /** Data file path relative to /data/ */
  dataPath: string;
  /** Chart rendering kind */
  kind: ArcChartKind;
  /** Data source attribution */
  source: string;
  /** Optional: log scale */
  scaleType?: "linear" | "log" | undefined;
  /** Optional: Y axis unit label */
  yUnit?: string;
  /** Optional: value key for line/valuation charts */
  valueKey?: string;
  /** Optional: value label */
  valueLabel?: string;
  /** Optional: series config for nested/multiline charts */
  series?: readonly ChartSeriesSpec[];
  /** Optional: annotation / caveat */
  note?: string;
  /** Optional: default eyebrow override */
  eyebrow?: string;
};

export type ChartSeriesSpec = {
  key: string;
  label: string;
  unit?: string;
  valueKey?: string;
  axis?: number;
};

// ─── Prose index entry ───

export type ProseEntry = {
  /** Content in Markdown or plain text */
  body: string;
};

export type ProseIndex = Record<string, ProseEntry>;
export type ChartIndex = Record<string, ChartIndexEntry>;
