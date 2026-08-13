import fs from "node:fs";
import path from "node:path";

export type Condition = {
  id: string;
  label: string;
  terms: string[];
};

export type SupportCategory = {
  id: string;
  label: string;
  terms: string[];
};

export type ResearchLead = {
  id: string;
  title: string;
  url: string;
  source: string;
  condition: string;
  supportCategory: string;
  query: string;
  found: string;
  description: string;
};

type ResearchConfig = {
  conditions: Condition[];
  support_categories: SupportCategory[];
  modifiers: string[];
};

const root = process.cwd();
const configPath = path.join(root, "research", "config", "categories.json");
const appsPath = path.join(root, "research", "apps");

export function getConfig(): ResearchConfig {
  return JSON.parse(fs.readFileSync(configPath, "utf-8"));
}

export function getConditions(): Condition[] {
  return getConfig().conditions;
}

export function getSupportCategories(): SupportCategory[] {
  return getConfig().support_categories;
}

export function getConditionLabel(conditionId: string): string {
  return getConditions().find((condition) => condition.id === conditionId)?.label ?? conditionId;
}

export function getCategoryLabel(categoryId: string): string {
  return getSupportCategories().find((category) => category.id === categoryId)?.label ?? categoryId;
}

let leadCache: ResearchLead[] | null = null;

export function getLeads(): ResearchLead[] {
  if (leadCache) {
    return leadCache;
  }

  if (!fs.existsSync(appsPath)) {
    leadCache = [];
    return leadCache;
  }

  const leads: ResearchLead[] = [];
  for (const condition of fs.readdirSync(appsPath)) {
    const conditionPath = path.join(appsPath, condition);
    if (!fs.statSync(conditionPath).isDirectory()) {
      continue;
    }

    for (const fileName of fs.readdirSync(conditionPath)) {
      if (!fileName.endsWith(".md")) {
        continue;
      }
      const supportCategory = fileName.replace(/\.md$/, "");
      const filePath = path.join(conditionPath, fileName);
      leads.push(...parseLeadFile(fs.readFileSync(filePath, "utf-8"), condition, supportCategory));
    }
  }

  leadCache = leads.sort((a, b) => b.found.localeCompare(a.found) || a.title.localeCompare(b.title));
  return leadCache;
}

export function getLeadsForCondition(conditionId: string): ResearchLead[] {
  return getLeads().filter((lead) => lead.condition === conditionId);
}

export function getLeadCounts(): Map<string, number> {
  const counts = new Map<string, number>();
  for (const lead of getLeads()) {
    counts.set(lead.condition, (counts.get(lead.condition) ?? 0) + 1);
  }
  return counts;
}

export type CoverageCell = {
  conditionId: string;
  conditionLabel: string;
  categoryId: string;
  categoryLabel: string;
  count: number;
  /** 0 when the lane is empty, otherwise 1..BIN_COUNT from the sequential ramp. */
  bin: number;
};

export type CoverageRow = {
  conditionId: string;
  conditionLabel: string;
  cells: CoverageCell[];
  total: number;
};

export type CoverageBin = {
  bin: number;
  min: number;
  max: number | null;
  label: string;
};

export type Coverage = {
  categories: SupportCategory[];
  rows: CoverageRow[];
  categoryTotals: { categoryId: string; categoryLabel: string; total: number }[];
  bins: CoverageBin[];
  total: number;
  max: number;
};

const BIN_COUNT = 5;

/**
 * Merged-lead counts for every condition x support category lane.
 *
 * Bins are equal-width over [1, max] rather than fixed thresholds, so the ramp keeps
 * its full range as the corpus grows instead of saturating at the dark end. The legend
 * renders the resolved ranges, so the reader always sees real numbers.
 */
export function getCoverage(): Coverage {
  const conditions = getConditions();
  const categories = getSupportCategories();
  const leads = getLeads();

  const counts = new Map<string, number>();
  for (const lead of leads) {
    const key = `${lead.condition}\u0000${lead.supportCategory}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const countFor = (conditionId: string, categoryId: string) =>
    counts.get(`${conditionId}\u0000${categoryId}`) ?? 0;

  let max = 0;
  for (const condition of conditions) {
    for (const category of categories) {
      max = Math.max(max, countFor(condition.id, category.id));
    }
  }

  const width = max > 0 ? max / BIN_COUNT : 1;
  const binFor = (count: number) =>
    count <= 0 ? 0 : Math.min(BIN_COUNT, Math.ceil(count / width));

  const bins: CoverageBin[] = Array.from({ length: BIN_COUNT }, (_, index) => {
    const min = Math.floor(index * width) + 1;
    const top = index === BIN_COUNT - 1 ? max : Math.floor((index + 1) * width);
    return {
      bin: index + 1,
      min,
      max: index === BIN_COUNT - 1 ? null : top,
      label: index === BIN_COUNT - 1 ? `${min}+` : `${min}–${top}`
    };
  });

  const rows: CoverageRow[] = conditions.map((condition) => {
    const cells = categories.map((category) => {
      const count = countFor(condition.id, category.id);
      return {
        conditionId: condition.id,
        conditionLabel: condition.label,
        categoryId: category.id,
        categoryLabel: category.label,
        count,
        bin: binFor(count)
      };
    });

    return {
      conditionId: condition.id,
      conditionLabel: condition.label,
      cells,
      total: cells.reduce((sum, cell) => sum + cell.count, 0)
    };
  });

  const categoryTotals = categories.map((category) => ({
    categoryId: category.id,
    categoryLabel: category.label,
    total: rows.reduce(
      (sum, row) => sum + (row.cells.find((cell) => cell.categoryId === category.id)?.count ?? 0),
      0
    )
  }));

  return {
    categories,
    rows,
    categoryTotals,
    bins,
    total: rows.reduce((sum, row) => sum + row.total, 0),
    max
  };
}

export function getLatestRun(conditionId: string): string | null {
  const runPath = path.join(root, "research", "runs", "conditions", `${conditionId}.md`);
  if (!fs.existsSync(runPath)) {
    return null;
  }
  return fs.readFileSync(runPath, "utf-8");
}

function parseLeadFile(markdown: string, condition: string, supportCategory: string): ResearchLead[] {
  const sections = markdown.split(/\n(?=### )/g);
  return sections.flatMap((section) => {
    const title = section.match(/^###\s+(.+)$/m)?.[1]?.trim();
    if (!title) {
      return [];
    }

    const field = (name: string) => {
      const match = section.match(new RegExp(`^- ${name}:\\s*(.*)$`, "m"));
      return match?.[1]?.trim() ?? "";
    };

    const url = field("URL");
    if (!url) {
      return [];
    }

    return [
      {
        id: `${condition}-${supportCategory}-${slugify(title)}-${slugify(url)}`,
        title,
        url,
        source: field("Source"),
        condition: field("Condition") || condition,
        supportCategory: field("Support category") || supportCategory,
        query: field("Query"),
        found: field("Found"),
        description: field("Description")
      }
    ];
  });
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/https?:\/\//, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80);
}
