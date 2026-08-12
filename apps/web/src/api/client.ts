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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (res.status === 204) {
    return undefined as T;
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (body as { detail?: string }).detail ?? res.statusText;
    throw new Error(detail);
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
