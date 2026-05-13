import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { Dashboard } from "./pages/Dashboard";
import { InvestigationDetail } from "./pages/InvestigationDetail";
import { SkillBrowser } from "./pages/SkillBrowser";
import { WikiBrowser } from "./pages/WikiBrowser";
import { KnowledgeBrowser } from "./pages/KnowledgeBrowser";
import { useInvestigations } from "./hooks/useInvestigations";
import { CreateInvestigationModal } from "./components/CreateInvestigationModal";
import { createInvestigation } from "./hooks/useInvestigations";

function AppLayout() {
  const { investigations, refresh } = useInvestigations();
  const [showModal, setShowModal] = useState(false);

  const handleCreate = async (
    actor: string,
    question: string,
    initialRead: string
  ) => {
    await createInvestigation(actor, question, initialRead);
    refresh();
    setShowModal(false);
  };

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-obsidian text-parchment">
      <Sidebar
        investigations={investigations}
        onCreate={() => setShowModal(true)}
      />
      <main className="flex-1 min-w-0 overflow-hidden">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route
            path="/investigation/:id"
            element={<InvestigationDetail />}
          />
          <Route path="/actors" element={<Dashboard />} />
          <Route path="/wiki" element={<WikiBrowser />} />
          <Route path="/knowledge" element={<KnowledgeBrowser />} />
          <Route path="/skills" element={<SkillBrowser />} />
        </Routes>
      </main>

      {showModal && (
        <CreateInvestigationModal
          onClose={() => setShowModal(false)}
          onCreate={handleCreate}
        />
      )}
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}
