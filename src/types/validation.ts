export type ValidationItem = {
  id: string;
  severity: string;
  message: string;
  source: string;
};

export type ValidationResponse = {
  items: ValidationItem[];
};