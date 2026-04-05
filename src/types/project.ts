export type TrustLevel =
  | "new"
  | "parsed"
  | "reviewed"
  | "validated"
  | "proven"
  | "trusted_template";

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
  value: string | null;
  package: string | null;
  manufacturer: string | null;
  mpn: string | null;
  description: string;
  trustLevel: TrustLevel;
  blockId: string | null;
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
  requirements: Requirement[];
  blocks: DesignBlock[];
  chatMessages: ChatMessage[];
};