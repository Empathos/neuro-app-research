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

export function getLeads(): ResearchLead[] {
  if (!fs.existsSync(appsPath)) {
    return [];
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

  return leads.sort((a, b) => b.found.localeCompare(a.found) || a.title.localeCompare(b.title));
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
