export type ComponentItem = {
  id: string;
  name: string;
  category: string;
  trustLevel: string;
  status: string;
};

export type ComponentsResponse = {
  items: ComponentItem[];
};