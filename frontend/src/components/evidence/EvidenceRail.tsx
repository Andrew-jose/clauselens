import React from 'react';
import { ShieldCheck, History, Info, X } from 'lucide-react';
import type { ClauseCitation } from '../../types';
import { EvidenceCard } from './EvidenceCard';

interface EvidenceRailProps {
  activeCitation?: ClauseCitation | null;
  citationHistory?: ClauseCitation[];
  documentName?: string;
  onJumpToDocument: (page: number, clauseId?: string | null, quote?: string) => void;
  onClearActive?: () => void;
}

export const EvidenceRail: React.FC<EvidenceRailProps> = ({
  activeCitation,
  citationHistory = [],
  documentName,
  onJumpToDocument,
  onClearActive,
}) => {
  return (
    <aside
      className="w-full lg:w-80 xl:w-96 flex flex-col bg-slate-50 border-l border-slate-200 h-full p-4 overflow-y-auto"
      aria-label="Evidence Ledger and Citation Rail"
    >
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-brand-100 text-brand-700">
            <ShieldCheck className="w-4 h-4" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Evidence Ledger</h2>
            <p className="text-[11px] text-slate-500">Verified document citations</p>
          </div>
        </div>

        {activeCitation && onClearActive && (
          <button
            onClick={onClearActive}
            className="p-1 text-slate-400 hover:text-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
            aria-label="Clear active citation"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        )}
      </div>

      {/* Active Selected Citation */}
      {activeCitation ? (
        <div className="mb-6 animate-fadeIn">
          <div className="flex items-center gap-1.5 text-xs font-bold text-brand-700 uppercase tracking-wider mb-2">
            <span>Active Focus Citation</span>
          </div>
          <EvidenceCard
            citation={activeCitation}
            documentName={documentName}
            onJumpToDocument={onJumpToDocument}
            className="ring-2 ring-brand-500 shadow-md bg-brand-50/20"
          />
        </div>
      ) : (
        <div className="mb-6 p-4 rounded-xl border border-dashed border-slate-300 bg-white/70 text-center">
          <Info className="w-6 h-6 text-slate-400 mx-auto mb-2" aria-hidden="true" />
          <h3 className="text-xs font-semibold text-slate-700">No Citation Selected</h3>
          <p className="text-[11px] text-slate-500 mt-1">
            Click any citation chip in Q&amp;A, Risk Radar, or Action Plan to inspect its verbatim excerpt.
          </p>
        </div>
      )}

      {/* Trust & Grounding Mechanism Note */}
      <div className="p-3 mb-6 rounded-xl bg-emerald-50/80 border border-emerald-200 text-emerald-950">
        <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-900 mb-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-700" aria-hidden="true" />
          <span>Code-Level Grounding Guarantee</span>
        </div>
        <p className="text-[11px] text-emerald-800 leading-relaxed">
          Every citation undergoes deterministic substring/fuzzy token verification (&ge;90% match) against stored document text. Unanchored claims are structurally blocked.
        </p>
      </div>

      {/* Citation History */}
      {citationHistory.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
            <History className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
            <span>Recent Citations ({citationHistory.length})</span>
          </div>
          <div className="space-y-3">
            {citationHistory.slice(0, 5).map((cit, idx) => (
              <EvidenceCard
                key={idx}
                citation={cit}
                documentName={documentName}
                onJumpToDocument={onJumpToDocument}
              />
            ))}
          </div>
        </div>
      )}
    </aside>
  );
};
