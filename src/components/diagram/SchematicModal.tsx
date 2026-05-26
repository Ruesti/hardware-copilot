import { useEffect, useState } from "react";
import { describeBlockCircuit } from "../../api/diagram";
import { setSchematicValidated } from "../../api/components";
import type { DiagramBlock, ComponentItem } from "../../types/project";

type Props = {
  projectId: string;
  block: DiagramBlock;
  components: ComponentItem[];
  onClose: () => void;
  /** Wird nach Validate/Regenerate aufgerufen, damit der Container den Block-State
   *  (schematicAscii, schematicValidated) lokal aktualisiert. */
  onBlockChange?: (next: Partial<DiagramBlock>) => void;
};

const COST_HINT =
  "≈ 500–1200 Tokens pro Generierung (~0,3–0,6 ¢ mit Sonnet 4.6)";

export function SchematicModal({ projectId, block, components, onClose, onBlockChange }: Props) {
  const [schematic, setSchematic] = useState<string | null>(block.schematicAscii ?? null);
  const [loading, setLoading] = useState(!block.schematicAscii);
  const [error, setError] = useState<string | null>(null);
  const [validated, setValidated] = useState<boolean>(block.schematicValidated);
  const [validating, setValidating] = useState(false);

  const blockComponents = components.filter((c) => c.blockId === block.id);

  useEffect(() => {
    if (block.schematicAscii) {
      setSchematic(block.schematicAscii);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    setSchematic(null);
    describeBlockCircuit(projectId, block.id)
      .then((res) => {
        setSchematic(res.schematic);
        onBlockChange?.({ schematicAscii: res.schematic, schematicValidated: false });
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
    // onBlockChange bewusst nicht in Deps — wäre instabil und würde Loop auslösen
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, block.id, block.schematicAscii]);

  useEffect(() => {
    setValidated(block.schematicValidated);
  }, [block.schematicValidated]);

  const handleRegenerate = () => {
    if (validated) {
      const ok = confirm(
        "Dieser Schaltplan ist als VALIDIERT markiert. Neu generieren würde ihn überschreiben und den Validierungs-Status zurücksetzen. Trotzdem fortfahren?"
      );
      if (!ok) return;
    }
    setLoading(true);
    setError(null);
    describeBlockCircuit(projectId, block.id)
      .then((res) => {
        setSchematic(res.schematic);
        setValidated(false);
        onBlockChange?.({ schematicAscii: res.schematic, schematicValidated: false });
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  };

  const handleToggleValidated = async () => {
    const next = !validated;
    setValidating(true);
    try {
      await setSchematicValidated(projectId, block.id, next);
      setValidated(next);
      onBlockChange?.({ schematicValidated: next });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setValidating(false);
    }
  };

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.7)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: 24,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#111114",
          border: "1px solid #3f3f46",
          borderRadius: 14,
          width: "100%",
          maxWidth: 680,
          maxHeight: "85vh",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          boxShadow: "0 24px 64px rgba(0,0,0,0.6)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid #27272a",
            display: "flex",
            alignItems: "flex-start",
            gap: 8,
            flexShrink: 0,
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <span style={{ fontSize: 16, fontWeight: 700, color: "#f4f4f5" }}>
                {block.name}
              </span>
              {validated && (
                <span
                  style={{
                    fontSize: 10,
                    color: "#86efac",
                    background: "#052e16",
                    border: "1px solid #166534",
                    borderRadius: 6,
                    padding: "2px 6px",
                    fontWeight: 600,
                    letterSpacing: "0.04em",
                  }}
                >
                  ✓ VALIDIERT
                </span>
              )}
            </div>
            <div style={{ fontSize: 13, color: "#71717a", lineHeight: 1.5 }}>
              {block.description}
            </div>
          </div>
          <button
            onClick={handleToggleValidated}
            disabled={validating || loading || !schematic}
            style={{
              background: validated ? "#052e16" : "transparent",
              border: `1px solid ${validated ? "#166534" : "#27272a"}`,
              color: validating || !schematic ? "#3f3f46" : validated ? "#86efac" : "#a1a1aa",
              cursor: validating || !schematic ? "not-allowed" : "pointer",
              fontSize: 11,
              padding: "4px 10px",
              borderRadius: 6,
              flexShrink: 0,
              fontWeight: 500,
            }}
            title={
              validated
                ? "Validierung aufheben"
                : "Diesen Schaltplan als geprüft markieren — wird beim Refresh nicht überschrieben"
            }
          >
            {validating ? "…" : validated ? "✓ Validiert" : "Validieren"}
          </button>
          <button
            onClick={handleRegenerate}
            disabled={loading}
            style={{
              background: "transparent",
              border: "1px solid #27272a",
              color: loading ? "#3f3f46" : "#a1a1aa",
              cursor: loading ? "not-allowed" : "pointer",
              fontSize: 11,
              padding: "4px 10px",
              borderRadius: 6,
              flexShrink: 0,
            }}
            title={`Schaltplan neu generieren\n${COST_HINT}`}
          >
            ↻
          </button>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "#71717a",
              cursor: "pointer",
              fontSize: 18,
              padding: "2px 6px",
              borderRadius: 6,
              flexShrink: 0,
            }}
          >
            ×
          </button>
        </div>

        {/* Scrollable body */}
        <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: "16px 20px" }}>
          <div style={{ marginBottom: 20 }}>
            <div
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: "#52525b",
                letterSpacing: "0.05em",
                textTransform: "uppercase",
                marginBottom: 10,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <span>Circuit Topology</span>
              <span
                style={{
                  fontSize: 10,
                  color: "#3f3f46",
                  textTransform: "none",
                  letterSpacing: 0,
                  fontWeight: 400,
                }}
                title={COST_HINT}
              >
                {COST_HINT}
              </span>
            </div>

            {loading && (
              <div style={{ fontSize: 13, color: "#52525b", padding: "12px 0" }}>
                Schaltplan wird erzeugt…
              </div>
            )}

            {error && (
              <div
                style={{
                  fontSize: 13,
                  color: "#f87171",
                  background: "#1c0a0a",
                  border: "1px solid #450a0a",
                  borderRadius: 8,
                  padding: "10px 12px",
                }}
              >
                {error}
              </div>
            )}

            {schematic && (
              <pre
                style={{
                  margin: 0,
                  fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
                  fontSize: 12,
                  lineHeight: 1.6,
                  color: "#a1a1aa",
                  background: "#0b0b0e",
                  border: "1px solid #27272a",
                  borderRadius: 8,
                  padding: "14px 16px",
                  whiteSpace: "pre",
                  overflowX: "auto",
                }}
              >
                {schematic}
              </pre>
            )}

            {!loading && !error && !schematic && (
              <button
                onClick={handleRegenerate}
                style={{
                  background: "transparent",
                  border: "1px solid #27272a",
                  borderRadius: 8,
                  color: "#a1a1aa",
                  padding: "10px 16px",
                  cursor: "pointer",
                  fontSize: 13,
                  width: "100%",
                }}
              >
                Schaltplan jetzt erzeugen ↗
              </button>
            )}
          </div>

          {/* Components section */}
          {blockComponents.length > 0 && (
            <div>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: "#52525b",
                  letterSpacing: "0.05em",
                  textTransform: "uppercase",
                  marginBottom: 10,
                }}
              >
                Components ({blockComponents.length})
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {blockComponents.map((c) => (
                  <div
                    key={c.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      padding: "8px 12px",
                      background: "#0c0c0f",
                      border: "1px solid #1f1f23",
                      borderRadius: 8,
                      flexWrap: "wrap",
                    }}
                  >
                    <span style={{ fontSize: 13, fontWeight: 500, color: "#e4e4e7", flex: 1, minWidth: 120 }}>
                      {c.name ?? c.description}
                    </span>

                    {c.type && (
                      <span
                        style={{
                          fontSize: 10,
                          color: "#60a5fa",
                          background: "#1e3a5f",
                          borderRadius: 4,
                          padding: "2px 6px",
                        }}
                      >
                        {c.type}
                      </span>
                    )}

                    {c.value && (
                      <span style={{ fontSize: 11, color: "#a1a1aa" }}>{c.value}</span>
                    )}

                    {c.package && (
                      <span style={{ fontSize: 11, color: "#71717a" }}>{c.package}</span>
                    )}

                    {c.mpn && (
                      <span
                        style={{
                          fontSize: 10,
                          color: "#52525b",
                          fontFamily: "monospace",
                        }}
                      >
                        {c.mpn}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {blockComponents.length === 0 && !loading && (
            <div style={{ fontSize: 12, color: "#3f3f46" }}>
              No components assigned to this block yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
