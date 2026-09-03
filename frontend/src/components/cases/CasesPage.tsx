import { useState } from "react";
import { CasesListPage } from "./CasesListPage";
import { CaseDetailPage } from "./CaseDetailPage";

export function CasesPage() {
  const [openCaseId, setOpenCaseId] = useState<string | null>(null);

  if (openCaseId) {
    return <CaseDetailPage caseId={openCaseId} onBack={() => setOpenCaseId(null)} />;
  }

  return <CasesListPage onOpenCase={setOpenCaseId} />;
}
