import { useState } from "react";
import { AppShell, type TabId } from "./components/layout/AppShell";

export default function App() {
  const [tab, setTab] = useState<TabId>("bestand");
  return <AppShell tab={tab} onTabChange={setTab} />;
}
