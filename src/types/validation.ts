export type ValidationSeverity =
  | "info"
  | "warning"
  | "error"
  | "review_required";

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