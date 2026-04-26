import { useEffect, useRef, useState } from "react";
import { fetchDatasheets, uploadDatasheet } from "../../api/datasheets";
import type { DatasheetRecord } from "../../types/project";

type Props = {
  projectId: string;
};

export function DatasheetPanel({ projectId }: Props) {
  const [datasheets, setDatasheets] = useState<DatasheetRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<DatasheetRecord | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchDatasheets(projectId)
      .then((res) => { if (!cancelled) setDatasheets(res.items); })
      .catch((err) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [projectId]);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    setUploading(true);
    setError(null);
    try {
      const result = await uploadDatasheet(projectId, file);
      const newRecord: DatasheetRecord = {
        id: result.id,
        projectId,
        componentId: null,
        filename: result.filename,
        extractedData: result.extractedData,
        createdAt: new Date().toISOString(),
      };
      setDatasheets((prev) => [newRecord, ...prev]);
      setSelected(newRecord);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", overflow: "hidden" }}>
      {/* Left: list + upload */}
      <div
        style={{
          width: 260,
          borderRight: "1px solid #18181b",
          display: "flex",
          flexDirection: "column",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            padding: "12px 16px",
            borderBottom: "1px solid #18181b",
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          Datasheets
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
            {datasheets.length}
          </span>
        </div>

        {/* Drop zone */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileRef.current?.click()}
          style={{
            margin: 12,
            border: "2px dashed #27272a",
            borderRadius: 10,
            padding: "16px 10px",
            textAlign: "center",
            cursor: uploading ? "not-allowed" : "pointer",
            background: "#0c0c0f",
            transition: "border-color 0.15s",
          }}
        >
          <div style={{ fontSize: 22, marginBottom: 6 }}>📄</div>
          <div style={{ fontSize: 12, color: "#52525b" }}>
            {uploading ? "Uploading & analyzing…" : "Drop PDF or click to upload"}
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            style={{ display: "none" }}
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>

        {error && (
          <div
            style={{
              margin: "0 12px 8px",
              padding: "8px 10px",
              background: "#3f1218",
              border: "1px solid #7f1d1d",
              borderRadius: 8,
              fontSize: 12,
              color: "#fca5a5",
            }}
          >
            {error}
          </div>
        )}

        {/* List */}
        <div style={{ flex: 1, overflowY: "auto", padding: "0 8px 8px" }}>
          {loading && (
            <div style={{ fontSize: 12, color: "#3f3f46", textAlign: "center", paddingTop: 16 }}>
              Loading…
            </div>
          )}
          {!loading && datasheets.length === 0 && (
            <div style={{ fontSize: 12, color: "#3f3f46", textAlign: "center", paddingTop: 16 }}>
              No datasheets uploaded yet.
            </div>
          )}
          {datasheets.map((ds) => (
            <button
              key={ds.id}
              onClick={() => setSelected(ds)}
              style={{
                width: "100%",
                background: selected?.id === ds.id ? "#18181b" : "transparent",
                border:
                  selected?.id === ds.id ? "1px solid #3f3f46" : "1px solid transparent",
                borderRadius: 8,
                padding: "8px 10px",
                textAlign: "left",
                cursor: "pointer",
                marginBottom: 2,
              }}
            >
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 500,
                  color: "#e4e4e7",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {ds.filename}
              </div>
              <div style={{ fontSize: 11, color: "#52525b", marginTop: 2 }}>
                {new Date(ds.createdAt).toLocaleDateString()}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Right: extracted data */}
      <div style={{ flex: 1, minWidth: 0, overflowY: "auto", padding: 20 }}>
        {!selected ? (
          <div
            style={{
              height: "100%",
              display: "grid",
              placeItems: "center",
              color: "#3f3f46",
              fontSize: 13,
            }}
          >
            Select a datasheet to view extracted data.
          </div>
        ) : (
          <DatasheetDetail record={selected} />
        )}
      </div>
    </div>
  );
}

function DatasheetDetail({ record }: { record: DatasheetRecord }) {
  const d = record.extractedData as Record<string, unknown>;

  const str = (v: unknown) => (typeof v === "string" ? v : null);
  const arr = (v: unknown): string[] =>
    Array.isArray(v) ? v.filter((x) => typeof x === "string") : [];
  const obj = (v: unknown): Record<string, string> =>
    v && typeof v === "object" && !Array.isArray(v)
      ? (v as Record<string, string>)
      : {};

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 760 }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: "#f4f4f5" }}>
          {str(d.component_name) ?? record.filename}
        </h2>
        {str(d.manufacturer) && (
          <div style={{ fontSize: 13, color: "#71717a", marginTop: 4 }}>
            {str(d.manufacturer)} · {str(d.mpn) ?? "—"}
          </div>
        )}
      </div>

      {str(d.description) && (
        <p style={{ margin: 0, fontSize: 13, color: "#a1a1aa", lineHeight: 1.6 }}>
          {d.description as string}
        </p>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
          gap: 10,
        }}
      >
        {[
          ["Package", str(d.package)],
          ["Supply Voltage", str(d.supply_voltage)],
          ["Max Current", str(d.max_current)],
          ["Operating Temp", str(d.operating_temp)],
        ]
          .filter(([, v]) => v)
          .map(([label, value]) => (
            <div
              key={label as string}
              style={{
                background: "#111114",
                border: "1px solid #1c1c1f",
                borderRadius: 8,
                padding: "10px 12px",
              }}
            >
              <div style={{ fontSize: 11, color: "#52525b", marginBottom: 4 }}>
                {label as string}
              </div>
              <div style={{ fontSize: 13, color: "#e4e4e7", fontWeight: 500 }}>
                {value as string}
              </div>
            </div>
          ))}
      </div>

      {arr(d.key_features).length > 0 && (
        <Section title="Key Features">
          <ul style={{ margin: 0, paddingLeft: 18, display: "flex", flexDirection: "column", gap: 4 }}>
            {arr(d.key_features).map((f, i) => (
              <li key={i} style={{ fontSize: 13, color: "#a1a1aa" }}>
                {f}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {Object.keys(obj(d.pinout)).length > 0 && (
        <Section title="Pinout">
          <KVTable data={obj(d.pinout)} />
        </Section>
      )}

      {Object.keys(obj(d.absolute_max_ratings)).length > 0 && (
        <Section title="Absolute Maximum Ratings">
          <KVTable data={obj(d.absolute_max_ratings)} />
        </Section>
      )}

      {str(d.typical_application) && (
        <Section title="Typical Application">
          <p style={{ margin: 0, fontSize: 13, color: "#a1a1aa", lineHeight: 1.6 }}>
            {d.typical_application as string}
          </p>
        </Section>
      )}

      {str(d.raw_analysis) && (
        <Section title="Raw Analysis">
          <pre
            style={{
              margin: 0,
              fontSize: 12,
              color: "#a1a1aa",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              background: "#0c0c0f",
              borderRadius: 8,
              padding: 12,
            }}
          >
            {str(d.raw_analysis)}
          </pre>
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div
        style={{
          fontSize: 12,
          fontWeight: 600,
          color: "#52525b",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          marginBottom: 8,
        }}
      >
        {title}
      </div>
      {children}
    </div>
  );
}

function KVTable({ data }: { data: Record<string, string> }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 2fr",
        gap: "1px",
        background: "#1c1c1f",
        border: "1px solid #1c1c1f",
        borderRadius: 8,
        overflow: "hidden",
      }}
    >
      {Object.entries(data).map(([k, v], i) => (
        <>
          <div
            key={`k-${i}`}
            style={{
              background: "#111114",
              padding: "7px 12px",
              fontSize: 12,
              color: "#71717a",
              fontFamily: "monospace",
            }}
          >
            {k}
          </div>
          <div
            key={`v-${i}`}
            style={{
              background: "#0c0c0f",
              padding: "7px 12px",
              fontSize: 12,
              color: "#e4e4e7",
            }}
          >
            {v}
          </div>
        </>
      ))}
    </div>
  );
}
