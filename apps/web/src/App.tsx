import { useEffect, useState } from "react";
import { api, TaxonomyNode, clearStoredAuth, getStoredAuth } from "./api/client";
import Login from "./pages/Login";

type Level = "zone" | "department" | "category" | "subcategory";

export default function App() {
  const [authed, setAuthed] = useState(() => Boolean(getStoredAuth()));

  if (!authed) {
    return <Login onLoggedIn={() => setAuthed(true)} />;
  }

  return (
    <TaxonomyApp
      onLogout={() => {
        clearStoredAuth();
        setAuthed(false);
      }}
    />
  );
}

function TaxonomyApp({ onLogout }: { onLogout: () => void }) {
  const [includeInactive, setIncludeInactive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [zones, setZones] = useState<TaxonomyNode[]>([]);
  const [departments, setDepartments] = useState<TaxonomyNode[]>([]);
  const [categories, setCategories] = useState<TaxonomyNode[]>([]);
  const [subcategories, setSubcategories] = useState<TaxonomyNode[]>([]);
  const [selectedZone, setSelectedZone] = useState<TaxonomyNode | null>(null);
  const [selectedDept, setSelectedDept] = useState<TaxonomyNode | null>(null);
  const [selectedCat, setSelectedCat] = useState<TaxonomyNode | null>(null);
  const [selectedSub, setSelectedSub] = useState<TaxonomyNode | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const selected: { level: Level; node: TaxonomyNode } | null = selectedSub
    ? { level: "subcategory", node: selectedSub }
    : selectedCat
      ? { level: "category", node: selectedCat }
      : selectedDept
        ? { level: "department", node: selectedDept }
        : selectedZone
          ? { level: "zone", node: selectedZone }
          : null;

  async function refreshZones() {
    const res = await api.listZones(includeInactive);
    setZones(res.items);
  }

  useEffect(() => {
    refreshZones().catch((e: Error) => setError(e.message));
  }, [includeInactive]);

  useEffect(() => {
    if (!selectedZone) {
      setDepartments([]);
      return;
    }
    api
      .listDepartments(selectedZone.id, includeInactive)
      .then((r) => setDepartments(r.items))
      .catch((e: Error) => setError(e.message));
  }, [selectedZone, includeInactive]);

  useEffect(() => {
    if (!selectedDept) {
      setCategories([]);
      return;
    }
    api
      .listCategories(selectedDept.id, includeInactive)
      .then((r) => setCategories(r.items))
      .catch((e: Error) => setError(e.message));
  }, [selectedDept, includeInactive]);

  useEffect(() => {
    if (!selectedCat) {
      setSubcategories([]);
      return;
    }
    api
      .listSubcategories(selectedCat.id, includeInactive)
      .then((r) => setSubcategories(r.items))
      .catch((e: Error) => setError(e.message));
  }, [selectedCat, includeInactive]);

  useEffect(() => {
    if (selected) {
      setName(selected.node.name);
      setDescription(selected.node.description ?? "");
    }
  }, [selected?.node.id]);

  async function onCreate(level: Level) {
    setError(null);
    try {
      const payload = { name, description: description || undefined };
      if (level === "zone") await api.createZone(payload);
      if (level === "department" && selectedZone)
        await api.createDepartment(selectedZone.id, payload);
      if (level === "category" && selectedDept)
        await api.createCategory(selectedDept.id, payload);
      if (level === "subcategory" && selectedCat)
        await api.createSubcategory(selectedCat.id, payload);
      setName("");
      setDescription("");
      await refreshZones();
      if (selectedZone) {
        const d = await api.listDepartments(selectedZone.id, includeInactive);
        setDepartments(d.items);
      }
      if (selectedDept) {
        const c = await api.listCategories(selectedDept.id, includeInactive);
        setCategories(c.items);
      }
      if (selectedCat) {
        const s = await api.listSubcategories(selectedCat.id, includeInactive);
        setSubcategories(s.items);
      }
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function onSave() {
    if (!selected) return;
    setError(null);
    try {
      const payload = { name, description: description || undefined };
      if (selected.level === "zone") await api.updateZone(selected.node.id, payload);
      if (selected.level === "department")
        await api.updateDepartment(selected.node.id, payload);
      if (selected.level === "category")
        await api.updateCategory(selected.node.id, payload);
      if (selected.level === "subcategory")
        await api.updateSubcategory(selected.node.id, payload);
      await refreshZones();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function onRetire() {
    if (!selected) return;
    if (
      !window.confirm(
        `Retire ${selected.node.name}? This node and all descendants will be deactivated.`,
      )
    ) {
      return;
    }
    setError(null);
    try {
      if (selected.level === "zone") await api.deleteZone(selected.node.id);
      if (selected.level === "department") await api.deleteDepartment(selected.node.id);
      if (selected.level === "category") await api.deleteCategory(selected.node.id);
      if (selected.level === "subcategory") await api.deleteSubcategory(selected.node.id);
      setSelectedSub(null);
      if (selected.level === "zone") setSelectedZone(null);
      if (selected.level === "department") setSelectedDept(null);
      if (selected.level === "category") setSelectedCat(null);
      await refreshZones();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function onRestore() {
    if (!selected) return;
    setError(null);
    try {
      if (selected.level === "zone") await api.restoreZone(selected.node.id);
      if (selected.level === "department") await api.restoreDepartment(selected.node.id);
      if (selected.level === "category") await api.restoreCategory(selected.node.id);
      if (selected.level === "subcategory") await api.restoreSubcategory(selected.node.id);
      await refreshZones();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  function renderList(
    title: string,
    items: TaxonomyNode[],
    onSelect: (n: TaxonomyNode) => void,
    selectedId?: string,
  ) {
    return (
      <section className="column">
        <h2>
          {title}
          <span className="count">{items.length}</span>
        </h2>
        {items.length === 0 ? <div className="empty">Empty</div> : null}
        <ul>
          {items.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className={item.is_active ? "" : "inactive"}
                aria-pressed={selectedId === item.id}
                onClick={() => onSelect(item)}
              >
                <span className="node-name">{item.name}</span>
                {!item.is_active ? <span className="badge">retired</span> : null}
              </button>
            </li>
          ))}
        </ul>
      </section>
    );
  }

  return (
    <div className="app">
      <div className="topbar">
        <div className="brand">
          <div className="brand-logo">RT</div>
          <div>
            <h1>Retail Taxonomy Console</h1>
            <p>Merchandise classification workspace</p>
          </div>
        </div>
        <div className="topbar-actions">
          <label className="toggle">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
            />
            Show inactive
          </label>
          <button type="button" className="btn btn-outline" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </div>

      {error ? (
        <div className="error" role="alert">
          {error}
        </div>
      ) : null}

      <div className="columns">
        {renderList(
          "Zones",
          zones,
          (n) => {
            setSelectedZone(n);
            setSelectedDept(null);
            setSelectedCat(null);
            setSelectedSub(null);
          },
          selectedZone?.id,
        )}
        {renderList(
          "Departments",
          departments,
          (n) => {
            setSelectedDept(n);
            setSelectedCat(null);
            setSelectedSub(null);
          },
          selectedDept?.id,
        )}
        {renderList(
          "Categories",
          categories,
          (n) => {
            setSelectedCat(n);
            setSelectedSub(null);
          },
          selectedCat?.id,
        )}
        {renderList("Subcategories", subcategories, setSelectedSub, selectedSub?.id)}
      </div>

      <section className="detail">
        <h2>Detail</h2>
        <p className="selected-line">
          Selected:{" "}
          {selected ? (
            <b>
              {selected.level} / {selected.node.name}
            </b>
          ) : (
            "none"
          )}
        </p>
        <div className="fields">
          <label className="field">
            <span>Name</span>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label className="field">
            <span>Description</span>
            <input value={description} onChange={(e) => setDescription(e.target.value)} />
          </label>
        </div>
        <div className="actions">
          <button type="button" className="btn btn-primary" onClick={() => onCreate("zone")}>
            Create zone
          </button>
          <button
            type="button"
            className="btn btn-primary"
            disabled={!selectedZone}
            onClick={() => onCreate("department")}
          >
            Create department
          </button>
          <button
            type="button"
            className="btn btn-primary"
            disabled={!selectedDept}
            onClick={() => onCreate("category")}
          >
            Create category
          </button>
          <button
            type="button"
            className="btn btn-primary"
            disabled={!selectedCat}
            onClick={() => onCreate("subcategory")}
          >
            Create subcategory
          </button>
          <button type="button" className="btn btn-ghost" disabled={!selected} onClick={onSave}>
            Save
          </button>
          <button
            type="button"
            className="btn btn-danger"
            disabled={!selected?.node.is_active}
            onClick={onRetire}
          >
            Retire
          </button>
          <button
            type="button"
            className="btn btn-restore"
            disabled={!selected || selected.node.is_active}
            onClick={onRestore}
          >
            Restore
          </button>
        </div>
      </section>
    </div>
  );
}
