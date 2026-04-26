import { useState } from "react";
import {
  createRequirement,
  updateRequirement,
  deleteRequirement,
} from "../../api/requirements";
import {
  createBlock,
  updateBlock,
  deleteBlock,
} from "../../api/blocks";
import { StatusBadge } from "../ui/StatusBadge";
import type { Requirement, DesignBlock, TrustLevel } from "../../types/project";

type Props = {
  projectId: string;
  requirements: Requirement[];
  blocks: DesignBlock[];
  onRequirementsChange: (items: Requirement[]) => void;
  onBlocksChange: (items: DesignBlock[]) => void;
};

export function SpecPanel({
  projectId,
  requirements,
  blocks,
  onRequirementsChange,
  onBlocksChange,
}: Props) {
  return (
    <div
      style={{
        flex: 1,
        minHeight: 0,
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 0,
        overflow: "hidden",
      }}
    >
      <RequirementsColumn
        projectId={projectId}
        items={requirements}
        onChange={onRequirementsChange}
      />
      <div style={{ borderLeft: "1px solid #18181b" }}>
        <BlocksColumn
          projectId={projectId}
          items={blocks}
          onChange={onBlocksChange}
        />
      </div>
    </div>
  );
}

// ── Requirements ──────────────────────────────────────────────────────────────

function RequirementsColumn({
  projectId,
  items,
  onChange,
}: {
  projectId: string;
  items: Requirement[];
  onChange: (items: Requirement[]) => void;
}) {
  const [adding, setAdding] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", description: "", status: "open" });

  const startAdd = () => {
    setForm({ title: "", description: "", status: "open" });
    setAdding(true);
    setEditId(null);
  };

  const startEdit = (r: Requirement) => {
    setForm({ title: r.title, description: r.description, status: r.status });
    setEditId(r.id);
    setAdding(false);
  };

  const handleSave = async () => {
    if (!form.title.trim()) return;
    if (adding) {
      const created = await createRequirement(projectId, form);
      onChange([...items, created]);
      setAdding(false);
    } else if (editId) {
      const updated = await updateRequirement(projectId, editId, form);
      onChange(items.map((r) => (r.id === editId ? updated : r)));
      setEditId(null);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteRequirement(projectId, id);
    onChange(items.filter((r) => r.id !== id));
    if (editId === id) setEditId(null);
  };

  const cancel = () => { setAdding(false); setEditId(null); };

  return (
    <div style={columnStyle}>
      <ColumnHeader
        title="Requirements"
        count={items.length}
        onAdd={startAdd}
      />
      <div style={{ flex: 1, overflowY: "auto", padding: "12px" }}>
        {items.map((r) =>
          editId === r.id ? (
            <InlineForm
              key={r.id}
              form={form}
              onChange={setForm}
              onSave={handleSave}
              onCancel={cancel}
              showStatus
            />
          ) : (
            <RequirementCard
              key={r.id}
              item={r}
              onEdit={() => startEdit(r)}
              onDelete={() => handleDelete(r.id)}
            />
          )
        )}
        {adding && (
          <InlineForm
            form={form}
            onChange={setForm}
            onSave={handleSave}
            onCancel={cancel}
            showStatus
          />
        )}
        {items.length === 0 && !adding && (
          <EmptyHint text="No requirements yet. Add the first one." />
        )}
      </div>
    </div>
  );
}

function RequirementCard({
  item,
  onEdit,
  onDelete,
}: {
  item: Requirement;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <div style={cardStyle}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 500, fontSize: 13, color: "#f4f4f5" }}>
            {item.title}
          </div>
          {item.description && (
            <div style={{ fontSize: 12, color: "#71717a", marginTop: 4, lineHeight: 1.5 }}>
              {item.description}
            </div>
          )}
        </div>
        <StatusBadge label={item.status} tone="neutral" />
      </div>
      <div style={cardActionsStyle}>
        <button style={linkBtnStyle} onClick={onEdit}>Edit</button>
        <button style={{ ...linkBtnStyle, color: "#ef4444" }} onClick={onDelete}>Delete</button>
      </div>
    </div>
  );
}

// ── Blocks ────────────────────────────────────────────────────────────────────

function BlocksColumn({
  projectId,
  items,
  onChange,
}: {
  projectId: string;
  items: DesignBlock[];
  onChange: (items: DesignBlock[]) => void;
}) {
  const [adding, setAdding] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", description: "", status: "new" });

  const startAdd = () => {
    setForm({ title: "", description: "", status: "new" });
    setAdding(true);
    setEditId(null);
  };

  const startEdit = (b: DesignBlock) => {
    setForm({ title: b.name, description: b.description, status: b.trustLevel });
    setEditId(b.id);
    setAdding(false);
  };

  const handleSave = async () => {
    if (!form.title.trim()) return;
    if (adding) {
      const created = await createBlock(projectId, {
        name: form.title,
        description: form.description,
        trustLevel: form.status as TrustLevel,
      });
      onChange([...items, created]);
      setAdding(false);
    } else if (editId) {
      const updated = await updateBlock(projectId, editId, {
        name: form.title,
        description: form.description,
        trustLevel: form.status as TrustLevel,
      });
      onChange(items.map((b) => (b.id === editId ? updated : b)));
      setEditId(null);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteBlock(projectId, id);
    onChange(items.filter((b) => b.id !== id));
    if (editId === id) setEditId(null);
  };

  const cancel = () => { setAdding(false); setEditId(null); };

  return (
    <div style={columnStyle}>
      <ColumnHeader title="Design Blocks" count={items.length} onAdd={startAdd} />
      <div style={{ flex: 1, overflowY: "auto", padding: "12px" }}>
        {items.map((b) =>
          editId === b.id ? (
            <InlineForm
              key={b.id}
              form={form}
              onChange={setForm}
              onSave={handleSave}
              onCancel={cancel}
              statusLabel="Trust Level"
              statusOptions={[
                "new", "parsed", "reviewed", "validated", "proven", "trusted_template",
              ]}
              showStatus
            />
          ) : (
            <BlockCard
              key={b.id}
              item={b}
              onEdit={() => startEdit(b)}
              onDelete={() => handleDelete(b.id)}
            />
          )
        )}
        {adding && (
          <InlineForm
            form={form}
            onChange={setForm}
            onSave={handleSave}
            onCancel={cancel}
            statusLabel="Trust Level"
            statusOptions={[
              "new", "parsed", "reviewed", "validated", "proven", "trusted_template",
            ]}
            showStatus
          />
        )}
        {items.length === 0 && !adding && (
          <EmptyHint text='No blocks yet. Use "Draft Circuit" in Chat or add manually.' />
        )}
      </div>
    </div>
  );
}

function BlockCard({
  item,
  onEdit,
  onDelete,
}: {
  item: DesignBlock;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <div style={cardStyle}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 500, fontSize: 13, color: "#f4f4f5" }}>
            {item.name}
          </div>
          {item.description && (
            <div style={{ fontSize: 12, color: "#71717a", marginTop: 4, lineHeight: 1.5 }}>
              {item.description}
            </div>
          )}
        </div>
        <StatusBadge label={item.trustLevel} tone={item.trustLevel} />
      </div>
      <div style={cardActionsStyle}>
        <button style={linkBtnStyle} onClick={onEdit}>Edit</button>
        <button style={{ ...linkBtnStyle, color: "#ef4444" }} onClick={onDelete}>Delete</button>
      </div>
    </div>
  );
}

// ── Shared UI ─────────────────────────────────────────────────────────────────

function ColumnHeader({
  title,
  count,
  onAdd,
}: {
  title: string;
  count: number;
  onAdd: () => void;
}) {
  return (
    <div
      style={{
        padding: "12px 16px",
        borderBottom: "1px solid #18181b",
        display: "flex",
        alignItems: "center",
        gap: 8,
        flexShrink: 0,
      }}
    >
      <span style={{ fontWeight: 600, fontSize: 14, flex: 1 }}>{title}</span>
      <span
        style={{
          fontSize: 11,
          color: "#52525b",
          background: "#18181b",
          borderRadius: 10,
          padding: "2px 8px",
        }}
      >
        {count}
      </span>
      <button
        onClick={onAdd}
        style={{
          background: "#18181b",
          border: "1px solid #3f3f46",
          color: "#a1a1aa",
          borderRadius: 7,
          padding: "4px 10px",
          cursor: "pointer",
          fontSize: 12,
        }}
      >
        + Add
      </button>
    </div>
  );
}

type FormState = { title: string; description: string; status: string };

function InlineForm({
  form,
  onChange,
  onSave,
  onCancel,
  showStatus,
  statusOptions = ["open", "closed", "wontfix"],
}: {
  form: FormState;
  onChange: (f: FormState) => void;
  onSave: () => void;
  onCancel: () => void;
  showStatus?: boolean;
  statusLabel?: string;
  statusOptions?: string[];
}) {
  return (
    <div
      style={{
        background: "#111114",
        border: "1px solid #3f3f46",
        borderRadius: 10,
        padding: 12,
        marginBottom: 8,
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      <input
        autoFocus
        value={form.title}
        onChange={(e) => onChange({ ...form, title: e.target.value })}
        placeholder="Title"
        style={inputStyle}
      />
      <textarea
        value={form.description}
        onChange={(e) => onChange({ ...form, description: e.target.value })}
        placeholder="Description (optional)"
        rows={2}
        style={{ ...inputStyle, resize: "none", lineHeight: 1.5 }}
      />
      {showStatus && (
        <select
          value={form.status}
          onChange={(e) => onChange({ ...form, status: e.target.value })}
          style={inputStyle}
        >
          {statusOptions.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      )}
      <div style={{ display: "flex", gap: 6 }}>
        <button
          onClick={onSave}
          disabled={!form.title.trim()}
          style={{
            flex: 1,
            background: "#2563eb",
            color: "#fff",
            border: "none",
            borderRadius: 7,
            padding: "6px",
            cursor: "pointer",
            fontSize: 12,
            opacity: form.title.trim() ? 1 : 0.4,
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
            padding: "6px",
            cursor: "pointer",
            fontSize: 12,
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function EmptyHint({ text }: { text: string }) {
  return (
    <div style={{ fontSize: 12, color: "#3f3f46", textAlign: "center", padding: "20px 0" }}>
      {text}
    </div>
  );
}

const columnStyle: React.CSSProperties = {
  height: "100%",
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
};

const cardStyle: React.CSSProperties = {
  background: "#111114",
  border: "1px solid #1c1c1f",
  borderRadius: 10,
  padding: "10px 12px",
  marginBottom: 8,
};

const cardActionsStyle: React.CSSProperties = {
  display: "flex",
  gap: 8,
  marginTop: 8,
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
