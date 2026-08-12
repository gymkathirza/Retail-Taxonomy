export type Level = "zone" | "department" | "category" | "subcategory";

export interface Node {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProblemDetail {
  title?: string;
  detail?: string;
  status?: number;
}

const V1 = "/api/v1";

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  const data = text ? JSON.parse(text) : undefined;
  if (!res.ok) {
    const problem = data as ProblemDetail;
    // Fixed shape console log for failed calls.
    console.error({ event: "api_error", status: res.status, path });
    throw new Error(problem?.detail || problem?.title || `Request failed (${res.status})`);
  }
  return data as T;
}

const collectionPath: Record<Level, (parentId: string) => string> = {
  zone: () => `${V1}/zones`,
  department: (zoneId) => `${V1}/zones/${zoneId}/departments`,
  category: (deptId) => `${V1}/departments/${deptId}/categories`,
  subcategory: (catId) => `${V1}/categories/${catId}/subcategories`,
};

const itemPath: Record<Level, string> = {
  zone: `${V1}/zones`,
  department: `${V1}/departments`,
  category: `${V1}/categories`,
  subcategory: `${V1}/subcategories`,
};

export async function listNodes(
  level: Level,
  parentId: string | null,
  includeInactive: boolean
): Promise<Node[]> {
  const base = level === "zone" ? collectionPath.zone("") : collectionPath[level](parentId!);
  const url = `${base}?include_inactive=${includeInactive}`;
  const data = await request<{ items: Node[] }>("GET", url);
  return data.items;
}

export function createNode(level: Level, parentId: string | null, body: { name: string; description?: string }) {
  const base = level === "zone" ? collectionPath.zone("") : collectionPath[level](parentId!);
  return request<Node>("POST", base, body);
}

export function updateNode(level: Level, id: string, body: { name: string; description?: string }) {
  return request<Node>("PUT", `${itemPath[level]}/${id}`, body);
}

export function retireNode(level: Level, id: string) {
  return request<void>("DELETE", `${itemPath[level]}/${id}`);
}

export function restoreNode(level: Level, id: string) {
  return request<Node>("POST", `${itemPath[level]}/${id}/restore`);
}

export interface Stats {
  zones: number;
  departments: number;
  categories: number;
  paths: number;
}

interface TreeNode {
  level: Level;
  children: TreeNode[];
}

export async function getStats(): Promise<Stats> {
  const data = await request<{ items: TreeNode[] }>("GET", `${V1}/taxonomy/tree`);
  const stats: Stats = { zones: 0, departments: 0, categories: 0, paths: 0 };
  for (const zone of data.items) {
    stats.zones += 1;
    for (const dept of zone.children) {
      stats.departments += 1;
      for (const cat of dept.children) {
        stats.categories += 1;
        stats.paths += cat.children.length; // subcategories = unique classification paths
      }
    }
  }
  return stats;
}
