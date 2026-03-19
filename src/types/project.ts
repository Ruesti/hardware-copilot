export type TrustLevel =
  | "new"
  | "parsed"
  | "reviewed"
  | "validated"
  | "proven"
  | "trusted_template";

export type ValidationSeverity = "error" | "warning" | "info";

export type Requirement = {
  id: string;
  text: string;
};

export type DesignBlock = {
  id: string;
  name: string;
  description?: string;
  status: "draft" | "reviewed" | "frozen";
};

export type ComponentItem = {
  id: string;
  ref: string;
  name: string;
  category: string;
  trustLevel: TrustLevel;
};

export type ValidationIssue = {
  id: string;
  title: string;
  description: string;
  severity: ValidationSeverity;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export type Selection =
  | { kind: "requirement"; id: string }
  | { kind: "block"; id: string }
  | { kind: "component"; id: string }
  | null;

export type ProjectState = {
  id: string;
  name: string;
  phase: "spec" | "draft" | "review" | "freeze" | "export";
  requirements: Requirement[];
  blocks: DesignBlock[];
  components: ComponentItem[];
  validationIssues: ValidationIssue[];
  chatMessages: ChatMessage[];
};