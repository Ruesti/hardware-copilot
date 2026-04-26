export type TrustLevel =
  | "new"
  | "parsed"
  | "reviewed"
  | "validated"
  | "proven"
  | "trusted_template";

export type ValidationSeverity =
  | "info"
  | "warning"
  | "error"
  | "review_required";

// ── Projects ──────────────────────────────────────────────────────────────────

export type ProjectListItem = {
  id: string;
  name: string;
  phase: string;
  createdAt: string;
};

export type Project = {
  id: string;
  name: string;
  phase: string;
  createdAt: string;
  updatedAt: string;
};

export type ProjectsListResponse = {
  items: ProjectListItem[];
};

// ── Requirements ──────────────────────────────────────────────────────────────

export type Requirement = {
  id: string;
  title: string;
  description: string;
  status: string;
};

export type RequirementsResponse = {
  items: Requirement[];
};

// ── Blocks ────────────────────────────────────────────────────────────────────

export type DesignBlock = {
  id: string;
  name: string;
  description: string;
  trustLevel: TrustLevel;
};

export type BlocksResponse = {
  items: DesignBlock[];
};

// ── Components ────────────────────────────────────────────────────────────────

export type ComponentItem = {
  id: string;
  name: string | null;
  type: string | null;
  value: string | null;
  package: string | null;
  manufacturer: string | null;
  mpn: string | null;
  description: string;
  trustLevel: TrustLevel;
  blockId: string | null;
};

export type ComponentsResponse = {
  items: ComponentItem[];
};

// ── Chat ──────────────────────────────────────────────────────────────────────

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
};

export type ChatHistoryResponse = {
  items: ChatMessage[];
};

// ── Validation ────────────────────────────────────────────────────────────────

export type ValidationIssue = {
  id: string;
  severity: ValidationSeverity;
  title: string;
  message: string;
  relatedKind: "requirement" | "block" | "component" | null;
  relatedId: string | null;
};

export type ValidationResponse = {
  items: ValidationIssue[];
};

// ── Diagram ───────────────────────────────────────────────────────────────────

export type DiagramBlock = {
  id: string;
  name: string;
  description: string;
  trustLevel: TrustLevel;
  posX: number;
  posY: number;
  componentCount: number;
};

export type BlockConnection = {
  id: string;
  sourceBlockId: string;
  targetBlockId: string;
  label: string;
  connType: string;
};

// ── Datasheets ────────────────────────────────────────────────────────────────

export type DatasheetRecord = {
  id: string;
  projectId: string;
  componentId: string | null;
  filename: string;
  extractedData: Record<string, unknown>;
  createdAt: string;
};

export type DatasheetsResponse = {
  items: DatasheetRecord[];
};

// ── Selection ─────────────────────────────────────────────────────────────────

export type RequirementSelection = { kind: "requirement"; id: string };
export type BlockSelection = { kind: "block"; id: string };
export type ComponentSelection = { kind: "component"; id: string };
export type Selection =
  | RequirementSelection
  | BlockSelection
  | ComponentSelection
  | null;

// ── Legacy (kept for compatibility) ──────────────────────────────────────────

export type ProjectState = {
  name: string;
  phase: string;
  chatMessages: ChatMessage[];
};
