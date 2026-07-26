import {
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptsDirectory = dirname(fileURLToPath(import.meta.url));
const projectDirectory = resolve(scriptsDirectory, "..", "..");
const sourceDirectory = resolve(projectDirectory, "data");
const targetDirectory = resolve(projectDirectory, "astro", "public", "data");
const policyPath = resolve(
  projectDirectory,
  "config",
  "public-data-policy.json",
);
const registryPath = resolve(
  projectDirectory,
  "config",
  "dataset-registry.json",
);
const policy = JSON.parse(readFileSync(policyPath, "utf8"));
const registry = JSON.parse(readFileSync(registryPath, "utf8"));
const publicFiles = new Set(
  Object.entries(policy.files)
    .filter(([, rule]) => rule.public === true)
    .map(([filename]) => filename),
);
const registeredPublicFiles = new Set(
  registry.groups
    .filter((group) => group.access?.public === true)
    .flatMap((group) => group.files),
);

const internalDistributionPattern =
  /internal research|internal-only|license-required|仅内部|待授权/i;

function stripInternalMetadata(value) {
  if (Array.isArray(value)) {
    return value.map(stripInternalMetadata);
  }
  if (value === null || typeof value !== "object") {
    return value;
  }
  return Object.fromEntries(
    Object.entries(value)
      .filter(([key, nestedValue]) => {
        if (key === "_license" || key === "_provenance") return false;
        if (key !== "distribution" || typeof nestedValue !== "string") {
          return true;
        }
        return !internalDistributionPattern.test(nestedValue);
      })
      .map(([key, nestedValue]) => [key, stripInternalMetadata(nestedValue)]),
  );
}

if (policy.default !== "deny" || registry.default_access !== "deny") {
  throw new Error("Public data synchronization requires default-deny policies");
}
for (const filename of publicFiles) {
  if (!registeredPublicFiles.has(filename)) {
    throw new Error(`Public policy references unapproved dataset: ${filename}`);
  }
}
for (const filename of registeredPublicFiles) {
  if (!publicFiles.has(filename)) {
    throw new Error(
      `Dataset registry public scope missing from policy: ${filename}`,
    );
  }
}

rmSync(targetDirectory, { force: true, recursive: true });
mkdirSync(targetDirectory, { recursive: true });

if (existsSync(sourceDirectory)) {
  for (const filename of publicFiles) {
    const sourcePath = resolve(sourceDirectory, filename);
    if (!existsSync(sourcePath)) continue;
    let data = stripInternalMetadata(
      JSON.parse(readFileSync(sourcePath, "utf8")),
    );
    if (filename === "source_catalog.json") {
      data = {
        schema_version: data.schema_version,
        sources: data.sources.map((source) => ({
          id: source.id,
          name: source.name,
          role: source.role,
          terms_url: source.terms_url,
          url: source.url,
        })),
      };
    }
    writeFileSync(
      resolve(targetDirectory, filename),
      `${JSON.stringify(data)}\n`,
      "utf8",
    );
  }
}
