import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptsDirectory = dirname(fileURLToPath(import.meta.url));
const astroDirectory = resolve(scriptsDirectory, "..");
const projectDirectory = resolve(astroDirectory, "..");
const registry = JSON.parse(
  readFileSync(resolve(projectDirectory, "config", "dataset-registry.json")),
);

const pageGroups = {
  nasdaq: [
    "nasdaq-composite-panels",
    "nasdaq-100-panels",
    "nasdaq-valuation-proxy",
  ],
  sp500: [
    "sp500-price-panels",
    "sp500-volatility-panel",
    "sp500-total-return",
    "cboe-volatility",
  ],
};

function filesFor(groupIds) {
  return registry.groups
    .filter((group) => groupIds.includes(group.id))
    .flatMap((group) => group.files);
}

function pageHtml(page) {
  return readFileSync(
    resolve(projectDirectory, "dist", page, "index.html"),
    "utf8",
  );
}

function auditDatasetReferences() {
  const missing = [];
  for (const [page, groupIds] of Object.entries(pageGroups)) {
    const html = pageHtml(page);
    for (const filename of filesFor(groupIds)) {
      if (!html.includes(`/data/${filename}`)) {
        missing.push(`${page}: ${filename}`);
      }
    }
  }
  return missing;
}

function auditCatalogAnchors() {
  const archive = pageHtml("archive");
  const links = archive.matchAll(/href="\/(sp500|nasdaq)\/#([^"]+)"/g);
  const missing = [];
  for (const link of links) {
    const [, page, anchor] = link;
    if (!pageHtml(page).includes(`id="${anchor}"`)) {
      missing.push(`/${page}/#${anchor}`);
    }
  }
  return missing;
}

const missingDatasets = auditDatasetReferences();
const missingAnchors = auditCatalogAnchors();
if (missingDatasets.length > 0 || missingAnchors.length > 0) {
  const messages = [
    ...missingDatasets.map((item) => `Missing dataset reference: ${item}`),
    ...missingAnchors.map((item) => `Missing catalog anchor: ${item}`),
  ];
  throw new Error(messages.join("\n"));
}

const datasetCount = Object.values(pageGroups)
  .map(filesFor)
  .reduce((total, files) => total + files.length, 0);
console.log(`Verified ${datasetCount} index datasets and all catalog anchors.`);
