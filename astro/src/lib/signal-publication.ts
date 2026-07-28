import regimeRotation from "../../../data/regime_rotation.json";
import { strategyLenses } from "@/lib/strategy-lenses";

type RegimeResearch = {
  dates: string[];
};

export const signalPublicationFlags = {
  executionPublished: false,
  historicalValidationPublished: false,
  subscriptionEnabled: false,
} as const;

const LOCKED_EXECUTION_FIELDS = [
  "当前方向",
  "目标仓位",
  "下一触发",
  "失效条件",
] as const;

const research = regimeRotation as RegimeResearch;
const sampleStart = research.dates.at(0) ?? "—";
const sampleEnd = research.dates.at(-1) ?? "—";

export type PublicSignalEngine = {
  cadence: string;
  code: string;
  dimension: string;
  lockedFields: typeof LOCKED_EXECUTION_FIELDS;
  title: string;
};

export type SignalPublication = {
  asOf: string;
  engines: PublicSignalEngine[];
  evidence: {
    observations: number;
    sampleEnd: string;
    sampleStart: string;
    status: string;
  };
  executionPublished: boolean;
  lockedFields: typeof LOCKED_EXECUTION_FIELDS;
  subscriptionEnabled: boolean;
};

export function loadSignalPublication(): SignalPublication {
  return {
    asOf: sampleEnd,
    engines: strategyLenses.map((strategy) => ({
      cadence: strategy.cadence,
      code: strategy.code,
      dimension: strategy.dimension,
      lockedFields: LOCKED_EXECUTION_FIELDS,
      title: strategy.title,
    })),
    evidence: {
      observations: research.dates.length,
      sampleEnd,
      sampleStart,
      status: signalPublicationFlags.historicalValidationPublished
        ? "历史验证结果已发布"
        : "公式未冻结，当前不发布信号值",
    },
    executionPublished: signalPublicationFlags.executionPublished,
    lockedFields: LOCKED_EXECUTION_FIELDS,
    subscriptionEnabled: signalPublicationFlags.subscriptionEnabled,
  };
}
