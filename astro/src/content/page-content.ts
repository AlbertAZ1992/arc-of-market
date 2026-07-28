import { chartIndex } from "@/content/chart-index";
import dowProse from "@/content/prose/dow.json";
import macroProse from "@/content/prose/macro.json";
import mag7Prose from "@/content/prose/mag7.json";
import nasdaqProse from "@/content/prose/nasdaq.json";
import sp500Prose from "@/content/prose/sp500.json";
import dowSchema from "@/content/schemas/dow.json";
import macroSchema from "@/content/schemas/macro.json";
import mag7Schema from "@/content/schemas/mag7.json";
import nasdaqSchema from "@/content/schemas/nasdaq.json";
import sp500Schema from "@/content/schemas/sp500.json";
import type {
  Block,
  ComponentName,
  PageSchema,
  ProseEntry,
  ProseIndex,
  ResolvedChapter,
  ResolvedPageContent,
} from "@/content/types";

type JsonObject = Record<string, unknown>;

const COMPONENTS = new Set<ComponentName>([
  "ConstituentChanges",
  "FinancialStress",
  "MacroDashboard",
  "Mag7Dashboard",
  "NdxRankings",
  "NdxCrossSection",
  "Sp500Composition",
  "Sp500CrossSection",
]);

function object(value: unknown, context: string): JsonObject {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError(`${context} must be an object`);
  }
  return value as JsonObject;
}

function string(value: unknown, context: string): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new TypeError(`${context} must be a non-empty string`);
  }
  return value;
}

function proseEntry(index: ProseIndex, key: string, context: string): ProseEntry {
  const entry = index.entries[key];
  if (!entry) throw new TypeError(`${context} references missing prose: ${key}`);
  return entry;
}

function validateBlock(value: unknown, context: string): Block {
  const block = object(value, context);
  const type = string(block["type"], `${context}.type`);
  if (type === "chart") {
    const chart = string(block["chart"], `${context}.chart`);
    if (!Object.hasOwn(chartIndex, chart)) {
      throw new TypeError(`${context} references missing chart: ${chart}`);
    }
    return { chart, type };
  }
  if (type === "component") {
    const component = string(block["component"], `${context}.component`);
    if (!COMPONENTS.has(component as ComponentName)) {
      throw new TypeError(`${context} references unsupported component: ${component}`);
    }
    return { component: component as ComponentName, type };
  }
  if (type === "prose") {
    return { prose: string(block["prose"], `${context}.prose`), type };
  }
  throw new TypeError(`${context}.type is unsupported: ${type}`);
}

function validateProse(value: unknown, context: string): ProseIndex {
  const prose = object(value, context);
  const entries = object(prose["entries"], `${context}.entries`);
  for (const [key, rawEntry] of Object.entries(entries)) {
    object(rawEntry, `${context}.entries.${key}`);
  }
  return value as ProseIndex;
}

function resolveChapter(
  value: unknown,
  index: ProseIndex,
  chapterIndex: number,
): ResolvedChapter {
  const context = `page.chapters[${chapterIndex}]`;
  const chapter = object(value, context);
  const blocksValue = chapter["blocks"];
  if (!Array.isArray(blocksValue)) {
    throw new TypeError(`${context}.blocks must be an array`);
  }
  const copyKey = string(chapter["copy"], `${context}.copy`);
  const blocks = blocksValue.map((block, blockIndex) => {
    const validated = validateBlock(block, `${context}.blocks[${blockIndex}]`);
    if (validated.type !== "prose") return validated;
    return {
      entry: proseEntry(index, validated.prose, context),
      key: validated.prose,
      type: "prose" as const,
    };
  });
  return {
    blocks,
    copy: proseEntry(index, copyKey, context),
    id: string(chapter["id"], `${context}.id`),
    label: string(chapter["label"], `${context}.label`),
    navLabel: string(chapter["navLabel"], `${context}.navLabel`),
  };
}

export function definePageContent(
  schemaValue: unknown,
  proseValue: unknown,
): ResolvedPageContent {
  const page = object(schemaValue, "page");
  const prose = validateProse(proseValue, "prose");
  const chaptersValue = page["chapters"];
  if (!Array.isArray(chaptersValue) || chaptersValue.length === 0) {
    throw new TypeError("page.chapters must be a non-empty array");
  }
  const heroKey = string(page["hero"], "page.hero");
  const seoKey = string(page["seo"], "page.seo");
  const hero = proseEntry(prose, heroKey, "page.hero");
  const seo = proseEntry(prose, seoKey, "page.seo");
  const chapters = chaptersValue.map((chapter, index) =>
    resolveChapter(chapter, prose, index),
  );
  const chapterIds = new Set(chapters.map((chapter) => chapter.id));
  if (chapterIds.size !== chapters.length) {
    throw new TypeError("page chapter ids must be unique");
  }
  return {
    chapters,
    hero: {
      eyebrow: string(hero.eyebrow, `${heroKey}.eyebrow`),
      headline: string(hero.title, `${heroKey}.title`),
      intro: string(hero.body, `${heroKey}.body`),
    },
    id: string(page["id"], "page.id"),
    route: string(page["route"], "page.route"),
    seo: {
      description: string(seo.description, `${seoKey}.description`),
      title: string(seo.title, `${seoKey}.title`),
    },
  };
}

export const pageContent = {
  dow: definePageContent(dowSchema, dowProse),
  macro: definePageContent(macroSchema, macroProse),
  mag7: definePageContent(mag7Schema, mag7Prose),
  nasdaq: definePageContent(nasdaqSchema, nasdaqProse),
  sp500: definePageContent(sp500Schema, sp500Prose),
} as const satisfies Record<string, ResolvedPageContent>;

const routes = Object.values(pageContent).map((page) => page.route);
if (new Set(routes).size !== routes.length) {
  throw new TypeError("page routes must be unique");
}

export type ContentPageKey = keyof typeof pageContent;
export type { PageSchema };
