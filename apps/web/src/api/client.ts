export type TaxonomyNode = {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  zone_id?: string;
  department_id?: string;
  category_id?: string;
};

const AUTH_KEY = "taxonomy_basic_auth";

// OAuth2/OIDC access token (Phase 2). Held in memory and set by the OIDC
// helper after login/refresh; preferred over Basic when present.
let bearerToken: string | null = null;

export function setBearerToken(token: string): void {
  bearerToken = token;
}

export function clearBearerToken(): void {
  bearerToken = null;
}

export function getBearerToken(): string | null {
  return bearerToken;
}

export function getStoredAuth(): string | null {
  return sessionStorage.getItem(AUTH_KEY);
}

export function setStoredAuth(username: string, password: string): void {
  const token = btoa(`${username}:${password}`);
  sessionStorage.setItem(AUTH_KEY, token);
}

export function clearStoredAuth(): void {
  sessionStorage.removeItem(AUTH_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const auth = getStoredAuth();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  // Prefer an OAuth2/OIDC Bearer token when a SSO session is active;
  // otherwise fall back to stored HTTP Basic credentials.
  if (bearerToken) {
    headers.Authorization = `Bearer ${bearerToken}`;
  } else if (auth) {
    headers.Authorization = `Basic ${auth}`;
  }
  const res = await fetch(path, {
    ...init,
    headers,
  });
  if (res.status === 204) {
    return undefined as T;
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    console.error(
      JSON.stringify({ event: "api_error", status: res.status, path }),
    );
    const detail = (body as { detail?: string }).detail ?? res.statusText;
    throw new Error(typeof detail === "string" ? detail : res.statusText);
  }
  return body as T;
}

export const api = {
  listZones: (includeInactive = false) =>
    request<{ items: TaxonomyNode[] }>(
      `/api/v1/zones${includeInactive ? "?include_inactive=true" : ""}`,
    ),
  createZone: (payload: { name: string; description?: string }) =>
    request<TaxonomyNode>("/api/v1/zones", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateZone: (id: string, payload: { name: string; description?: string }) =>
    request<TaxonomyNode>(`/api/v1/zones/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteZone: (id: string) =>
    request<void>(`/api/v1/zones/${id}`, { method: "DELETE" }),
  restoreZone: (id: string) =>
    request<TaxonomyNode>(`/api/v1/zones/${id}/restore`, { method: "POST" }),

  listDepartments: (zoneId: string, includeInactive = false) =>
    request<{ items: TaxonomyNode[] }>(
      `/api/v1/zones/${zoneId}/departments${includeInactive ? "?include_inactive=true" : ""}`,
    ),
  createDepartment: (zoneId: string, payload: { name: string; description?: string }) =>
    request<TaxonomyNode>(`/api/v1/zones/${zoneId}/departments`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateDepartment: (id: string, payload: { name: string; description?: string }) =>
    request<TaxonomyNode>(`/api/v1/departments/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteDepartment: (id: string) =>
    request<void>(`/api/v1/departments/${id}`, { method: "DELETE" }),
  restoreDepartment: (id: string) =>
    request<TaxonomyNode>(`/api/v1/departments/${id}/restore`, { method: "POST" }),

  listCategories: (departmentId: string, includeInactive = false) =>
    request<{ items: TaxonomyNode[] }>(
      `/api/v1/departments/${departmentId}/categories${includeInactive ? "?include_inactive=true" : ""}`,
    ),
  createCategory: (departmentId: string, payload: { name: string; description?: string }) =>
    request<TaxonomyNode>(`/api/v1/departments/${departmentId}/categories`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateCategory: (id: string, payload: { name: string; description?: string }) =>
    request<TaxonomyNode>(`/api/v1/categories/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteCategory: (id: string) =>
    request<void>(`/api/v1/categories/${id}`, { method: "DELETE" }),
  restoreCategory: (id: string) =>
    request<TaxonomyNode>(`/api/v1/categories/${id}/restore`, { method: "POST" }),

  listSubcategories: (categoryId: string, includeInactive = false) =>
    request<{ items: TaxonomyNode[] }>(
      `/api/v1/categories/${categoryId}/subcategories${includeInactive ? "?include_inactive=true" : ""}`,
    ),
  createSubcategory: (categoryId: string, payload: { name: string; description?: string }) =>
    request<TaxonomyNode>(`/api/v1/categories/${categoryId}/subcategories`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateSubcategory: (id: string, payload: { name: string; description?: string }) =>
    request<TaxonomyNode>(`/api/v1/subcategories/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteSubcategory: (id: string) =>
    request<void>(`/api/v1/subcategories/${id}`, { method: "DELETE" }),
  restoreSubcategory: (id: string) =>
    request<TaxonomyNode>(`/api/v1/subcategories/${id}/restore`, { method: "POST" }),
};
