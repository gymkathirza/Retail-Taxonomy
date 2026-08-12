import { useCallback, useEffect, useState } from "react";
import {
  createNode,
  listNodes,
  restoreNode,
  retireNode,
  updateNode,
  type Level,
  type Node,
} from "./api/client";

const LEVELS: Level[] = ["zone", "department", "category", "subcategory"];
const TITLES: Record<Level, string> = {
  zone: "Zones",
  department: "Departments",
  category: "Categories",
  subcategory: "Subcategories",
};

interface ColumnState {
  nodes: Node[];
  selectedId: string | null;
}

const emptyColumn = (): ColumnState => ({ nodes: [], selectedId: null });

export default function App() {
  const [columns, setColumns] = useState<Record<Level, ColumnState>>({
    zone: emptyColumn(),
    department: emptyColumn(),
    category: emptyColumn(),
    subcategory: emptyColumn(),
  });
  const [includeInactive, setIncludeInactive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<string>("checking…");

  const parentIdFor = useCallback(
    (level: Level, cols: Record<Level, ColumnState>): string | null => {
      if (level === "zone") return null;
      const parentLevel = LEVELS[LEVELS.indexOf(level) - 1];
      return cols[parentLevel].selectedId;
    },
    []
  );

  const loadLevel = useCallback(
    async (level: Level, cols: Record<Level, ColumnState>, inactive: boolean) => {
      const parentId = parentIdFor(level, cols);
      if (level !== "zone" && !parentId) return [] as Node[];
      return listNodes(level, parentId, inactive);
    },
    [parentIdFor]
  );

  const refreshFrom = useCallback(
    async (startLevel: Level, base: Record<Level, ColumnState>, inactive: boolean) => {
      const next = { ...base };
      let start = LEVELS.indexOf(startLevel);
      for (let i = start; i < LEVELS.length; i++) {
        const level = LEVELS[i];
        try {
          const nodes = await loadLevel(level, next, inactive);
          const keepSelected = nodes.some((n) => n.id === next[level].selectedId)
            ? next[level].selectedId
            : null;
          next[level] = { nodes, selectedId: keepSelected };
        } catch (e) {
          setError((e as Error).message);
          next[level] = emptyColumn();
        }
        if (!next[level].selectedId) {
          for (let j = i + 1; j < LEVELS.length; j++) next[LEVELS[j]] = emptyColumn();
          break;
        }
      }
      setColumns(next);
    },
    [loadLevel]
  );

  useEffect(() => {
    fetch("/health")
      .then((r) => (r.ok ? "healthy" : "down"))
      .then(setHealth)
      .catch(() => setHealth("down"));
    refreshFrom("zone", columns, includeInactive);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    refreshFrom("zone", columns, includeInactive);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [includeInactive]);

  const select = (level: Level, id: string) => {
    const next = { ...columns, [level]: { ...columns[level], selectedId: id } };
    setError(null);
    refreshFrom(level, next, includeInactive);
  };

  const handleCreate = async (level: Level, name: string) => {
    setError(null);
    try {
      await createNode(level, parentIdFor(level, columns), { name });
      await refreshFrom(level, columns, includeInactive);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const handleRename = async (level: Level, node: Node) => {
    const name = window.prompt(`Rename ${level}`, node.name);
    if (!name || name === node.name) return;
    setError(null);
    try {
      await updateNode(level, node.id, { name });
      await refreshFrom(level, columns, includeInactive);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const handleRetire = async (level: Level, node: Node) => {
    if (!window.confirm(`Retire "${node.name}" and all its descendants?`)) return;
    setError(null);
    try {
      await retireNode(level, node.id);
      await refreshFrom(level, columns, includeInactive);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const handleRestore = async (level: Level, node: Node) => {
    setError(null);
    try {
      await restoreNode(level, node.id);
      await refreshFrom(level, columns, includeInactive);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="app">
      <div className="topbar">
        <h1>Retail Taxonomy Console</h1>
        <div style={{ display: "flex", gap: 20, alignItems: "center" }}>
          <label>
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
            />
            Show inactive
          </label>
          <span className="status">API: {health}</span>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="columns">
        {LEVELS.map((level, idx) => {
          const parentId = parentIdFor(level, columns);
          const enabled = level === "zone" || !!parentId;
          const selected = columns[level].nodes.find((n) => n.id === columns[level].selectedId) || null;
          return (
            <Column
              key={level}
              level={level}
              title={TITLES[level]}
              enabled={enabled}
              nodes={columns[level].nodes}
              selectedId={columns[level].selectedId}
              onSelect={(id) => select(level, id)}
              onCreate={(name) => handleCreate(level, name)}
              onRename={(n) => handleRename(level, n)}
              onRetire={(n) => handleRetire(level, n)}
              onRestore={(n) => handleRestore(level, n)}
              selected={selected}
              placeholder={idx === 0 ? "New zone…" : `New ${level}…`}
            />
          );
        })}
      </div>
    </div>
  );
}

interface ColumnProps {
  level: Level;
  title: string;
  enabled: boolean;
  nodes: Node[];
  selectedId: string | null;
  selected: Node | null;
  placeholder: string;
  onSelect: (id: string) => void;
  onCreate: (name: string) => void;
  onRename: (n: Node) => void;
  onRetire: (n: Node) => void;
  onRestore: (n: Node) => void;
}

function Column(props: ColumnProps) {
  const [draft, setDraft] = useState("");

  if (!props.enabled) {
    return (
      <div className="column">
        <h2>{props.title}</h2>
        <div className="empty">Select a parent to view.</div>
      </div>
    );
  }

  const submit = () => {
    const name = draft.trim();
    if (!name) return;
    props.onCreate(name);
    setDraft("");
  };

  return (
    <div className="column">
      <h2>{props.title}</h2>
      <ul>
        {props.nodes.length === 0 && <li className="empty">No items yet.</li>}
        {props.nodes.map((n) => (
          <li
            key={n.id}
            className={`${n.id === props.selectedId ? "selected" : ""} ${n.is_active ? "" : "inactive"}`}
            onClick={() => props.onSelect(n.id)}
          >
            <span className="node-name">{n.name}</span>
            {!n.is_active && <span className="badge">retired</span>}
          </li>
        ))}
      </ul>
      {props.selected && (
        <div className="actions">
          <button className="btn-ghost" onClick={() => props.onRename(props.selected!)}>
            Edit
          </button>
          {props.selected.is_active ? (
            <button className="btn-danger" onClick={() => props.onRetire(props.selected!)}>
              Retire
            </button>
          ) : (
            <button className="btn-restore" onClick={() => props.onRestore(props.selected!)}>
              Restore
            </button>
          )}
        </div>
      )}
      <div className="add-row">
        <input
          value={draft}
          placeholder={props.placeholder}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button className="btn-primary" style={{ width: "100%" }} onClick={submit}>
          Add
        </button>
      </div>
    </div>
  );
}
