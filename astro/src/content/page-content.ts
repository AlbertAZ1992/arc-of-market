import dowContent from "@/content/prose/dow.json";
import macroContent from "@/content/prose/macro.json";
import mag7Content from "@/content/prose/mag7.json";
import nasdaqContent from "@/content/prose/nasdaq.json";
import sp500Content from "@/content/prose/sp500.json";
import type { PageSchema } from "@/content/types";

type JsonObject = Record<string, unknown>;

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

function validateBlock(value: unknown, context: string): void {
  const block = object(value, context);
  const type = string(block["type"], `${context}.type`);
  if (type === "chart") {
    string(block["chart"], `${context}.chart`);
    return;
  }
  if (type === "component") {
    string(block["component"], `${context}.component`);
    return;
  }
  if (type === "prose") {
    string(block["content"], `${context}.content`);
    return;
  }
  throw new TypeError(`${context}.type is unsupported: ${type}`);
}

export function definePageContent(value: unknown): PageSchema {
  const page = object(value, "page");
  const seo = object(page["seo"], "page.seo");
  const hero = object(page["hero"], "page.hero");
  const chapters = page["chapters"];
  if (!Array.isArray(chapters) || chapters.length === 0) {
    throw new TypeError("page.chapters must be a non-empty array");
  }
  chapters.forEach((chapterValue, chapterIndex) => {
    const context = `page.chapters[${chapterIndex}]`;
    const chapter = object(chapterValue, context);
    for (const field of ["id", "navLabel", "label", "title"] as const) {
      string(chapter[field], `${context}.${field}`);
    }
    const blocks = chapter["blocks"];
    if (!Array.isArray(blocks)) {
      throw new TypeError(`${context}.blocks must be an array`);
    }
    blocks.forEach((block, blockIndex) =>
      validateBlock(block, `${context}.blocks[${blockIndex}]`),
    );
  });
  string(page["route"], "page.route");
  string(seo["title"], "page.seo.title");
  string(seo["description"], "page.seo.description");
  string(hero["eyebrow"], "page.hero.eyebrow");
  string(hero["headline"], "page.hero.headline");
  string(hero["intro"], "page.hero.intro");
  return value as PageSchema;
}

export const pageContent = {
  dow: definePageContent(dowContent),
  macro: definePageContent(macroContent),
  mag7: definePageContent(mag7Content),
  nasdaq: definePageContent(nasdaqContent),
  sp500: definePageContent(sp500Content),
} as const;
