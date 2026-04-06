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

export type RequirementsResponse = {
  items: Requirement[];
};

export type DesignBlock = {
  id: string;
  name: string;
  description: string;
  trustLevel: TrustLevel;
};

export type BlocksResponse = {
  items: DesignBlock[];
};

export type ComponentItem = {
  id: string;
  name: string;
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

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
};

export type RequirementSelection = {
  kind: "requirement";
  id: string;
};

export type BlockSelection = {
  kind: "block";
  id: string;
};

export type ComponentSelection = {
  kind: "component";
  id: string;
};

export type Selection =
  | RequirementSelection
  | BlockSelection
  | ComponentSelection
  | null;

export type ProjectState = {
  name: string;
  phase: string;
  chatMessages: ChatMessage[];
};