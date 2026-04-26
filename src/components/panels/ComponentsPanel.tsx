import { useState } from "react";
import { createComponent, updateComponent, deleteComponent, fetchComponentDatasheet } from "../../api/components";
import { StatusBadge } from "../ui/StatusBadge";
import type { ComponentItem, DesignBlock, TrustLevel } from "../../types/project";

type Props = {
  projectId: string;
  components: ComponentItem[];
  blocks: DesignBlock[];
  onComponentsChange: (items: ComponentItem[]) => void;
  onBlocksChange: (items: DesignBlock[]) => void;
  onDatasheetFetched?: () => void;
};

const TRUST_ORDER: TrustLevel[] = [
  "new", "parsed", "reviewed", "validated", "proven", "trusted_template",
];

const TYPE_LABELS: Record<string, string> = {
  mcu: "MCU",
  power_ic: "Power IC",
  diode: "Diode",
  transistor: "Transistor",
  passive_resistor: "Resistor",
  passive_capacitor: "Capacitor",
  passive_inductor: "Inductor",
  sensor: "Sensor",
  connector: "Connector",
  protection: "Protection",
  memory: "Memory",
  crystal: "Crystal",
  other: "Other",
};

export function ComponentsPanel({
  projectId,
  components,
  blocks,
  onComponentsChange,
  onDatasheetFetched,
}: Props) {
  const [filterBlock, setFilterBlock] = useState<string>("all");
  const [filterTrust, setFilterTrust] = useState<string>("all");
  const [adding, setAdding] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [fetchingId, setFetchingId] = useState<string | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [fetchedIds, setFetchedIds] = useState<Set<string>>(new Set());

  const handleFetchDatasheet = async (cmpId: string) => {
    setFetchingId(cmpId);
    setFetchError(null);
    try {
      await fetchComponentDatasheet(projectId, cmpId);
      setFetchedIds((prev) => new Set([...prev, cmpId]));
      onDatasheetFetched?.();
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : String(err));
    } finally {
      setFetchingId(null);
    }
  };

  const defaultForm = () => ({
    name: "",
    type: "",
    value: "",
    package: "",
    manufacturer: "",
    mpn: "",
    description: "",
    trustLevel: "new" as TrustLevel,
    blockId: "",
  });

  const [form, setForm] = useState(defaultForm());

  const filtered = components.filter((c) => {
    if (filterBlock !== "all" && c.blockId !== filterBlock) return false;
    if (filterTrust !== "all" && c.trustLevel !== filterTrust) return false;
    return true;
  });

  const startAdd = () => {
    setForm(defaultForm());
    setAdding(true);
    setEditId(null);
  };

  const startEdit = (c: ComponentItem) => {
    setForm({
      name: c.name ?? "",
      type: c.type ?? "",
      value: c.value ?? "",
      package: c.package ?? "",
      manufacturer: c.manufacturer ?? "",
      mpn: c.mpn ?? "",
      description: c.description,
      trustLevel: c.trustLevel,
      blockId: c.blockId ?? "",
    });
    setEditId(c.id);
    setAdding(false);
  };

  const handleSave = async () => {
    if (!form.name.trim()) return;
    const payload = {
      name: form.name,
      type: form.type || undefined,
      value: form.value || undefined,
      package: form.package || undefined,
      manufacturer: form.manufacturer || undefined,
      mpn: form.mpn || undefined,
      description: form.description,
      trustLevel: form.trustLevel,
      blockId: form.blockId || undefined,
    };

    if (adding) {
      const created = await createComponent(projectId, payload);
      onComponentsChange([...components, created]);
      setAdding(false);
    } else if (editId) {
      const updated = await updateComponent(projectId, editId, payload);
      onComponentsChange(components.map((c) => (c.id === editId ? updated : c)));
      setEditId(null);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteComponent(projectId, id);
    onComponentsChange(components.filter((c) => c.id !== id));
    if (editId === id) setEditId(null);
  };

  const cancel = () => { setAdding(false); setEditId(null); };

  const blockName = (id: string | null) =>
    blocks.find((b) => b.id === id)?.name ?? "—";

  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      {/* Toolbar */}
      <div
        style={{
          padding: "10px 16px",
          borderBottom: "1px solid #18181b",
          display: "flex",
          alignItems: "center",
          gap: 10,
          flexShrink: 0,
        }}
      >
        <span style={{ fontWeight: 600, fontSize: 14 }}>
          Components
          <span
            style={{
              fontSize: 11,
              color: "#52525b",
              background: "#18181b",
              borderRadius: 10,
              padding: "2px 8px",
              marginLeft: 8,
            }}
          >
            {filtered.length}/{components.length}
          </span>
        </span>

        <div style={{ flex: 1 }} />

        <select
          value={filterBlock}
          onChange={(e) => setFilterBlock(e.target.value)}
          style={selectStyle}
        >
          <option value="all">All Blocks</option>
          {blocks.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>

        <select
          value={filterTrust}
          onChange={(e) => setFilterTrust(e.target.value)}
          style={selectStyle}
        >
          <option value="all">All Trust Levels</option>
          {TRUST_ORDER.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>

        <button
          onClick={startAdd}
          style={{
            background: "#18181b",
            border: "1px solid #3f3f46",
            color: "#a1a1aa",
            borderRadius: 7,
            padding: "5px 12px",
            cursor: "pointer",
            fontSize: 12,
          }}
        >
          + Add
        </button>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: "auto", padding: 16 }}>
        {fetchError && (
          <div
            style={{
              marginBottom: 12,
              padding: "8px 12px",
              background: "#3f1218",
              border: "1px solid #7f1d1d",
              borderRadius: 8,
              fontSize: 12,
              color: "#fca5a5",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>{fetchError}</span>
            <button
              onClick={() => setFetchError(null)}
              style={{ background: "none", border: "none", color: "#fca5a5", cursor: "pointer" }}
            >
              ✕
            </button>
          </div>
        )}
        {adding && (
          <ComponentForm
            form={form}
            onChange={setForm}
            onSave={handleSave}
            onCancel={cancel}
            blocks={blocks}
          />
        )}

        {filtered.length === 0 && !adding && (
          <div style={{ fontSize: 12, color: "#3f3f46", textAlign: "center", paddingTop: 32 }}>
            No components match the current filters.
          </div>
        )}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: 10,
          }}
        >
          {filtered.map((c) =>
            editId === c.id ? (
              <div key={c.id} style={{ gridColumn: "1 / -1" }}>
                <ComponentForm
                  form={form}
                  onChange={setForm}
                  onSave={handleSave}
                  onCancel={cancel}
                  blocks={blocks}
                />
              </div>
            ) : (
              <ComponentCard
                key={c.id}
                component={c}
                blockName={blockName(c.blockId)}
                isFetching={fetchingId === c.id}
                hasFetchedDatasheet={fetchedIds.has(c.id)}
                onEdit={() => startEdit(c)}
                onDelete={() => handleDelete(c.id)}
                onFetchDatasheet={c.mpn ? () => handleFetchDatasheet(c.id) : undefined}
              />
            )
          )}
        </div>
      </div>
    </div>
  );
}

function ComponentCard({
  component: c,
  blockName,
  isFetching,
  hasFetchedDatasheet,
  onEdit,
  onDelete,
  onFetchDatasheet,
}: {
  component: ComponentItem;
  blockName: string;
  isFetching: boolean;
  hasFetchedDatasheet: boolean;
  onEdit: () => void;
  onDelete: () => void;
  onFetchDatasheet?: () => void;
}) {
  return (
    <div
      style={{
        background: "#111114",
        border: "1px solid #1c1c1f",
        borderRadius: 10,
        padding: "12px",
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: 13, color: "#f4f4f5" }}>
            {c.name ?? "—"}
          </div>
          {c.mpn && (
            <div style={{ fontSize: 12, color: "#60a5fa", marginTop: 2, fontFamily: "monospace" }}>
              {c.mpn}
            </div>
          )}
        </div>
        <StatusBadge label={c.trustLevel} tone={c.trustLevel} />
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
        {c.type && (
          <span style={tagStyle("#1e293b", "#334155")}>
            {TYPE_LABELS[c.type] ?? c.type}
          </span>
        )}
        {c.package && (
          <span style={tagStyle("#1e1e2e", "#2d2d4e")}>{c.package}</span>
        )}
        {c.manufacturer && (
          <span style={tagStyle("#1a2a1a", "#2d4a2d")}>{c.manufacturer}</span>
        )}
        {c.value && (
          <span style={tagStyle("#2a1a2a", "#4a2d4a")}>{c.value}</span>
        )}
      </div>

      {c.description && (
        <div style={{ fontSize: 12, color: "#71717a", lineHeight: 1.4 }}>
          {c.description}
        </div>
      )}

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          paddingTop: 4,
          borderTop: "1px solid #1c1c1f",
        }}
      >
        <span style={{ fontSize: 11, color: "#3f3f46", flex: 1 }}>
          {blockName !== "—" ? `↳ ${blockName}` : "No block"}
        </span>
        {onFetchDatasheet && (
          <button
            style={{
              ...linkBtnStyle,
              color: hasFetchedDatasheet ? "#22c55e" : isFetching ? "#52525b" : "#60a5fa",
            }}
            onClick={onFetchDatasheet}
            disabled={isFetching}
            title={hasFetchedDatasheet ? "Datasheet loaded" : "Fetch datasheet from Nexar/Octopart"}
          >
            {isFetching ? "⟳ Fetching…" : hasFetchedDatasheet ? "✓ DS" : "↓ DS"}
          </button>
        )}
        <button style={linkBtnStyle} onClick={onEdit}>Edit</button>
        <button style={{ ...linkBtnStyle, color: "#ef4444" }} onClick={onDelete}>Delete</button>
      </div>
    </div>
  );
}

type FormState = {
  name: string;
  type: string;
  value: string;
  package: string;
  manufacturer: string;
  mpn: string;
  description: string;
  trustLevel: TrustLevel;
  blockId: string;
};

function ComponentForm({
  form,
  onChange,
  onSave,
  onCancel,
  blocks,
}: {
  form: FormState;
  onChange: (f: FormState) => void;
  onSave: () => void;
  onCancel: () => void;
  blocks: DesignBlock[];
}) {
  const f = (key: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    onChange({ ...form, [key]: e.target.value });

  return (
    <div
      style={{
        background: "#111114",
        border: "1px solid #3f3f46",
        borderRadius: 10,
        padding: 14,
        marginBottom: 12,
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 8,
      }}
    >
      <Field label="Name *">
        <input autoFocus value={form.name} onChange={f("name")} placeholder="e.g. Buck Regulator" style={inputStyle} />
      </Field>
      <Field label="Type">
        <select value={form.type} onChange={f("type")} style={inputStyle}>
          <option value="">— select type —</option>
          {Object.entries(TYPE_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </Field>
      <Field label="MPN">
        <input value={form.mpn} onChange={f("mpn")} placeholder="e.g. MP1584EN" style={inputStyle} />
      </Field>
      <Field label="Manufacturer">
        <input value={form.manufacturer} onChange={f("manufacturer")} placeholder="e.g. MPS" style={inputStyle} />
      </Field>
      <Field label="Value">
        <input value={form.value} onChange={f("value")} placeholder="e.g. 100nF" style={inputStyle} />
      </Field>
      <Field label="Package">
        <input value={form.package} onChange={f("package")} placeholder="e.g. SOIC-8" style={inputStyle} />
      </Field>
      <Field label="Trust Level">
        <select value={form.trustLevel} onChange={f("trustLevel")} style={inputStyle}>
          {["new", "parsed", "reviewed", "validated", "proven", "trusted_template"].map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </Field>
      <Field label="Block">
        <select value={form.blockId} onChange={f("blockId")} style={inputStyle}>
          <option value="">— no block —</option>
          {blocks.map((b) => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>
      </Field>
      <div style={{ gridColumn: "1 / -1" }}>
        <Field label="Description">
          <textarea
            value={form.description}
            onChange={f("description")}
            placeholder="Brief description"
            rows={2}
            style={{ ...inputStyle, resize: "none", lineHeight: 1.5 }}
          />
        </Field>
      </div>
      <div style={{ gridColumn: "1 / -1", display: "flex", gap: 8 }}>
        <button
          onClick={onSave}
          disabled={!form.name.trim()}
          style={{
            flex: 1,
            background: "#2563eb",
            color: "#fff",
            border: "none",
            borderRadius: 7,
            padding: "7px",
            cursor: "pointer",
            fontSize: 13,
            opacity: form.name.trim() ? 1 : 0.4,
          }}
        >
          Save
        </button>
        <button
          onClick={onCancel}
          style={{
            flex: 1,
            background: "#27272a",
            color: "#a1a1aa",
            border: "none",
            borderRadius: 7,
            padding: "7px",
            cursor: "pointer",
            fontSize: 13,
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <label style={{ fontSize: 11, color: "#52525b" }}>{label}</label>
      {children}
    </div>
  );
}

function tagStyle(bg: string, border: string): React.CSSProperties {
  return {
    fontSize: 11,
    padding: "2px 7px",
    borderRadius: 6,
    background: bg,
    border: `1px solid ${border}`,
    color: "#a1a1aa",
    whiteSpace: "nowrap",
  };
}

const selectStyle: React.CSSProperties = {
  background: "#111114",
  color: "#a1a1aa",
  border: "1px solid #27272a",
  borderRadius: 7,
  padding: "5px 8px",
  fontSize: 12,
  cursor: "pointer",
};

const linkBtnStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  cursor: "pointer",
  fontSize: 12,
  color: "#52525b",
  padding: 0,
};

const inputStyle: React.CSSProperties = {
  background: "#09090b",
  color: "#f4f4f5",
  border: "1px solid #27272a",
  borderRadius: 7,
  padding: "7px 10px",
  fontSize: 13,
  outline: "none",
  width: "100%",
  boxSizing: "border-box",
  fontFamily: "inherit",
};
