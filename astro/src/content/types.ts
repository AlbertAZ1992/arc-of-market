import type { ArcChartKind } from "@/lib/arc-chart-types";

export type ChartBlock = {
  chart: string;
  type: "chart";
};

export type ProseBlock = {
  prose: string;
  type: "prose";
};

export type ComponentName =
  | "ConstituentChanges"
  | "FinancialStress"
  | "MacroDashboard"
  | "Mag7Dashboard"
  | "NdxRankings"
  | "NdxCrossSection"
  | "Sp500Composition"
  | "Sp500CrossSection";

export type ComponentBlock = {
  component: ComponentName;
  type: "component";
};

export type Block = ChartBlock | ComponentBlock | ProseBlock;

export type ChapterSpec = {
  blocks: Block[];
  copy: string;
  id: string;
  label: string;
  navLabel: string;
};

export type PageSchema = {
  chapters: ChapterSpec[];
  hero: string;
  id: string;
  route: string;
  seo: string;
};

export type ProseEntry = {
  body?: string;
  caveat?: string;
  description?: string;
  eyebrow?: string;
  guide?: string;
  historicalContext?: string;
  title?: string;
  whatChanges?: string[];
  whyItMatters?: string;
};

export type ProseIndex = {
  entries: Record<string, ProseEntry>;
};

export type ResolvedProseBlock = {
  entry: ProseEntry;
  key: string;
  type: "prose";
};

export type ResolvedChapter = Omit<ChapterSpec, "blocks" | "copy"> & {
  blocks: Array<ChartBlock | ComponentBlock | ResolvedProseBlock>;
  copy: ProseEntry;
};

export type ResolvedPageContent = {
  chapters: ResolvedChapter[];
  hero: {
    eyebrow: string;
    headline: string;
    intro: string;
  };
  id: string;
  route: string;
  seo: {
    description: string;
    title: string;
  };
};

export type ChartSeriesSpec = {
  axis?: number;
  key: string;
  label: string;
  unit?: string;
  valueKey?: string;
};

export type ChartIndexEntry = {
  cadence?: "daily" | "monthly" | "quarterly" | "static";
  dataPath: string;
  description?: string;
  eyebrow?: string;
  homepageEligible?: boolean;
  interpretation?: readonly string[];
  kind: ArcChartKind;
  note?: string;
  scaleType?: "linear" | "log";
  series?: readonly ChartSeriesSpec[];
  source: string;
  title: string;
  valueKey?: string;
  valueLabel?: string;
  whatToWatch?: readonly string[];
  yUnit?: string;
};

export type ChartIndex = Record<string, ChartIndexEntry>;
