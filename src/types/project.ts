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

export type Requirement = {
  id: string;
  title: string;
  description: string;
  status: string;
};

export type DesignBlock = {
  id: string;
  name: string;
  description: string;
  trustLevel: TrustLevel;
};

export type ComponentItem = {
  id: string;
  name: string;
  value?: string | null;
  package?: string | null;
  manufacturer?: string | null;
  mpn?: string | null;
  description: string;
  trustLevel: TrustLevel;
  blockId?: string | null;
};

export type ValidationIssue = {
  id: string;
  severity: ValidationSeverity;
  title: string;
  message: string;
  relatedKind?: "requirement" | "block" | "component" | null;
  relatedId?: string | null;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
};

export type Selection =
  | { kind: "requirement"; id: string }
  | { kind: "block"; id: string }
  | { kind: "component"; id: string }
  | null;

export type ProjectState = {
  name: string;
  phase: string;
  requirements: Requirement[];
  blocks: DesignBlock[];
  components: ComponentItem[];
  validationIssues: ValidationIssue[];
  chatMessages: ChatMessage[];
};