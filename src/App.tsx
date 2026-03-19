import { useState } from "react";
import { AppShell } from "./components/layout/AppShell";
import { mockProject } from "./data/mockProject";
import type { Selection } from "./types/project";

export default function App() {
  const [selection, setSelection] = useState<Selection>({
    kind: "component",
    id: "c1",
  });

  return (
    <AppShell
      project={mockProject}
      selection={selection}
      onSelect={setSelection}
    />
  );
}