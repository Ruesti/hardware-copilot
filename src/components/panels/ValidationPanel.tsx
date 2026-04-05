import { useEffect, useState } from "react";
import { fetchValidation } from "../../api/validation";
import type { ValidationIssue } from "../../types/validation";
import { Panel } from "../ui/Panel";

export default function ValidationPanel() {
  const [items, setItems] = useState<ValidationIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const data = await fetchValidation();

        if (!cancelled) {
          setItems(data.items);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Panel title="Validation">
      {loading && <div>Loading validation...</div>}

      {!loading && error && <div>Failed to load validation: {error}</div>}

      {!loading && !error && items.length === 0 && <div>No validation items</div>}

      {!loading && !error && items.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {items.map((item) => (
            <div
              key={item.id}
              style={{
                border: "1px solid #333",
                borderRadius: 8,
                padding: 10,
              }}
            >
              <div style={{ fontWeight: 600 }}>
                {item.severity.toUpperCase()} — {item.title}
              </div>
              <div>{item.message}</div>
              {item.relatedKind && item.relatedId && (
                <div style={{ opacity: 0.7, fontSize: 12 }}>
                  {item.relatedKind}: {item.relatedId}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}