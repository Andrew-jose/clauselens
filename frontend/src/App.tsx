import { useEffect, useState } from 'react';
import {
  checkHealth,
  checkGeminiHealth,
  getDocuments,
  getDocumentChunks,
  getClauses,
  getFindings,
  askQuestion,
  compareLeases,
  submitSituation,
  getActionPlan,
  getLawyerQuestions,
  getExportPdfUrl,
} from './api/client';
import type {
  DocumentItem,
  DocumentChunk,
  ClauseItem,
  FindingItem,
  MessageItem,
  ClauseCitation,
  SituationClassification,
  ActionPlanData,
  LawyerQuestionsData,
} from './types';
import { Header } from './components/shared/Header';
import { Footer } from './components/shared/Footer';
import { UploadModal } from './components/shared/UploadModal';
import { AnalysisDashboard } from './components/dashboard/AnalysisDashboard';
import { DocumentViewer } from './components/document/DocumentViewer';
import { EvidenceRail } from './components/evidence/EvidenceRail';
import { RiskPanel } from './components/risk/RiskPanel';
import { ClauseExplorer } from './components/clauses/ClauseExplorer';
import { AskDocument } from './components/chat/AskDocument';
import { SituationPanel } from './components/situation/SituationPanel';
import { CompareView } from './components/compare/CompareView';
import { LawyerPrepView } from './components/lawyer/LawyerPrepView';
import { Upload, ShieldCheck } from 'lucide-react';

export default function App() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [clauses, setClauses] = useState<ClauseItem[]>([]);
  const [findings, setFindings] = useState<FindingItem[]>([]);
  const [situation, setSituation] = useState<SituationClassification | null>(null);
  const [actionPlan, setActionPlan] = useState<ActionPlanData | null>(null);
  const [lawyerQuestions, setLawyerQuestions] = useState<LawyerQuestionsData | null>(null);

  const [activeCitation, setActiveCitation] = useState<ClauseCitation | null>(null);
  const [citationHistory, setCitationHistory] = useState<ClauseCitation[]>([]);

  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<MessageItem[]>([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [isSituationLoading, setIsSituationLoading] = useState(false);
  const [isCompareLoading, setIsCompareLoading] = useState(false);

  const [apiConnected, setApiConnected] = useState(true);
  const [geminiConnected, setGeminiConnected] = useState(false);

  // Initial Health & Documents Load
  useEffect(() => {
    async function init() {
      try {
        const [h, g] = await Promise.allSettled([checkHealth(), checkGeminiHealth()]);
        if (h.status === 'fulfilled') setApiConnected(true);
        if (g.status === 'fulfilled' && g.value.status === 'ok') setGeminiConnected(true);

        const docs = await getDocuments();
        setDocuments(docs);
        if (docs.length > 0) {
          setSelectedDocId(docs[0].id);
        }
      } catch (err) {
        console.error('Initial load failed:', err);
      }
    }
    init();
  }, []);

  // When selected document changes, load all related data
  useEffect(() => {
    if (!selectedDocId) return;

    async function loadDocumentData() {
      try {
        const [cList, clList, fList, planRes, qRes] = await Promise.allSettled([
          getDocumentChunks(selectedDocId),
          getClauses(selectedDocId),
          getFindings(selectedDocId),
          getActionPlan(selectedDocId),
          getLawyerQuestions(selectedDocId),
        ]);

        if (cList.status === 'fulfilled') setChunks(cList.value);
        if (clList.status === 'fulfilled') setClauses(clList.value);
        if (fList.status === 'fulfilled') setFindings(fList.value);
        if (planRes.status === 'fulfilled') {
          setActionPlan(planRes.value);
          if (planRes.value.situation_type && planRes.value.urgency) {
            setSituation({
              situation_type: planRes.value.situation_type,
              urgency: planRes.value.urgency,
              relevant_categories: ['termination_penalties', 'term_renewal'],
            });
          }
        }
        if (qRes.status === 'fulfilled') setLawyerQuestions(qRes.value);
      } catch (err) {
        console.error('Error loading document details:', err);
      }
    }

    loadDocumentData();
  }, [selectedDocId]);

  const selectedDocument = documents.find((d) => d.id === selectedDocId);

  // Citation handler
  const handleSelectCitation = (citation: ClauseCitation) => {
    setActiveCitation(citation);
    setCitationHistory((prev) => {
      const exists = prev.some((c) => c.quote === citation.quote && c.page === citation.page);
      if (exists) return prev;
      return [citation, ...prev].slice(0, 10);
    });
  };

  const handleJumpToDocument = (page: number, clauseId?: string | null, quote?: string) => {
    setActiveCitation({ page, clause_id: clauseId, quote: quote || '' });
    setActiveTab('viewer');
  };

  // Q&A Question Send Handler
  const handleSendMessage = async (question: string) => {
    if (!selectedDocId) return;
    const userMsg: MessageItem = {
      id: String(Date.now()),
      role: 'user',
      content: question,
    };
    setChatMessages((prev) => [...prev, userMsg]);
    setIsChatLoading(true);

    try {
      const resp = await askQuestion(selectedDocId, question);
      const assistantMsg: MessageItem = {
        id: resp.message_id || String(Date.now() + 1),
        role: 'assistant',
        content: resp.answer,
        status: resp.status,
        citations: resp.citations,
        confidence_note: resp.confidence_note,
      };
      setChatMessages((prev) => [...prev, assistantMsg]);

      // If citations returned, set the first as active focus
      if (resp.citations && resp.citations.length > 0) {
        handleSelectCitation(resp.citations[0]);
      }
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          role: 'assistant',
          content: `Error answering question: ${err.message}`,
          status: 'not_found_in_document',
        },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Situation Submit Handler
  const handleSubmitSituation = async (contextText: string) => {
    if (!selectedDocId) return;
    setIsSituationLoading(true);
    try {
      const sit = await submitSituation(selectedDocId, contextText);
      setSituation(sit);

      // Refresh Action Plan & Lawyer Questions
      const [updatedPlan, updatedQs] = await Promise.all([
        getActionPlan(selectedDocId),
        getLawyerQuestions(selectedDocId),
      ]);
      setActionPlan(updatedPlan);
      setLawyerQuestions(updatedQs);
    } catch (err) {
      console.error('Failed submitting situation:', err);
    } finally {
      setIsSituationLoading(false);
    }
  };

  // Comparison Run Handler
  const handleCompare = async (docAId: string, docBId: string) => {
    setIsCompareLoading(true);
    try {
      return await compareLeases(docAId, docBId);
    } catch (err) {
      console.error('Comparison error:', err);
    } finally {
      setIsCompareLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans selection:bg-brand-500 selection:text-white">
      {/* Accessible Keyboard Skip Link (A2) */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-brand-600 focus:text-white focus:font-semibold focus:rounded-lg focus:shadow-xl focus:outline-none focus:ring-2 focus:ring-brand-400 focus:ring-offset-2 transition-transform"
      >
        Skip to main content
      </a>

      {/* Navbar Header */}
      <Header
        documents={documents}
        selectedDocumentId={selectedDocId}
        onSelectDocument={setSelectedDocId}
        onOpenUploadModal={() => setIsUploadModalOpen(true)}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        apiConnected={apiConnected}
        geminiConnected={geminiConnected}
      />

      {/* Main Workspace Layout */}
      <main id="main-content" tabIndex={-1} className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col outline-none">
        {documents.length === 0 ? (
          /* Empty State: Landing Hero */
          <div className="my-auto text-center py-16 px-4 max-w-2xl mx-auto space-y-6 animate-fadeIn">
            <div className="w-16 h-16 rounded-2xl bg-brand-600 text-white flex items-center justify-center mx-auto shadow-lg">
              <ShieldCheck className="w-9 h-9" aria-hidden="true" />
            </div>

            <div>
              <h1 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight">
                Clause<span className="text-brand-600">Lens</span>
              </h1>
              <p className="text-sm sm:text-base text-slate-600 mt-2 font-medium">
                Every claim, traced to the clause it came from.
              </p>
              <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-md mx-auto leading-relaxed">
                An evidence-first tenancy assistant with an independent code-level citation validator. Understand your residential lease before signing.
              </p>
            </div>

            <div className="pt-2">
              <button
                onClick={() => setIsUploadModalOpen(true)}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all"
              >
                <Upload className="w-4 h-4" aria-hidden="true" />
                <span>Upload Your Lease (PDF/DOCX)</span>
              </button>
            </div>
          </div>
        ) : selectedDocument ? (
          /* Active Document Workspace (Split: Main Tab Pane + Evidence Rail) */
          <div className="flex-1 flex flex-col lg:flex-row gap-6 min-h-[calc(100vh-12rem)]">
            {/* Left/Center Workspace */}
            <div className="flex-1 flex flex-col min-w-0">
              {activeTab === 'dashboard' && (
                <AnalysisDashboard
                  document={selectedDocument}
                  findings={findings}
                  clauses={clauses}
                  onNavigate={setActiveTab}
                  onSelectFindingCitation={(quote, page, clauseId) =>
                    handleSelectCitation({ quote, page, clause_id: clauseId })
                  }
                />
              )}

              {activeTab === 'viewer' && (
                <div className="h-[750px]">
                  <DocumentViewer
                    chunks={chunks}
                    documentName={selectedDocument.filename}
                    activeCitation={activeCitation}
                    onSelectClause={(clauseId, quote) => {
                      setActiveCitation({ page: 1, clause_id: clauseId, quote: quote || '' });
                    }}
                  />
                </div>
              )}

              {activeTab === 'risk' && (
                <RiskPanel
                  findings={findings}
                  onSelectCitation={(quote, page, clauseId) => {
                    handleSelectCitation({ quote, page, clause_id: clauseId });
                    setActiveTab('viewer');
                  }}
                  onAskAboutClause={(q) => {
                    setActiveTab('ask');
                    handleSendMessage(q);
                  }}
                />
              )}

              {activeTab === 'clauses' && (
                <ClauseExplorer
                  clauses={clauses}
                  onSelectClause={(clauseId, quote, page) => {
                    handleSelectCitation({
                      clause_id: clauseId,
                      quote: quote || '',
                      page: page || 1,
                    });
                    setActiveTab('viewer');
                  }}
                />
              )}

              {activeTab === 'ask' && (
                <div className="h-[750px]">
                  <AskDocument
                    messages={chatMessages}
                    onSendMessage={handleSendMessage}
                    onSelectCitation={handleSelectCitation}
                    isLoading={isChatLoading}
                  />
                </div>
              )}

              {activeTab === 'situation' && (
                <SituationPanel
                  situation={situation}
                  actionPlan={actionPlan}
                  onSubmitSituation={handleSubmitSituation}
                  onSelectCitation={handleSelectCitation}
                  onNavigateToLawyer={() => setActiveTab('lawyer')}
                  isLoading={isSituationLoading}
                />
              )}

              {activeTab === 'compare' && (
                <CompareView
                  documents={documents}
                  currentDocId={selectedDocId}
                  onCompare={handleCompare}
                  onSelectCitation={handleSelectCitation}
                  isLoading={isCompareLoading}
                />
              )}

              {activeTab === 'lawyer' && (
                <LawyerPrepView
                  document={selectedDocument}
                  questionsData={lawyerQuestions}
                  exportPdfUrl={getExportPdfUrl(selectedDocId)}
                />
              )}
            </div>

            {/* Right Evidence Rail (Permanently Linked) */}
            <div className="lg:w-80 xl:w-96 shrink-0 h-[750px] sticky top-20">
              <EvidenceRail
                activeCitation={activeCitation}
                citationHistory={citationHistory}
                documentName={selectedDocument.filename}
                onJumpToDocument={handleJumpToDocument}
                onClearActive={() => setActiveCitation(null)}
              />
            </div>
          </div>
        ) : null}
      </main>

      {/* Upload Modal Dialog */}
      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={(doc) => {
          setDocuments((prev) => [doc, ...prev]);
          setSelectedDocId(doc.id);
          setActiveTab('dashboard');
        }}
      />

      {/* Persistent Legal Safety Footer */}
      <Footer />
    </div>
  );
}
