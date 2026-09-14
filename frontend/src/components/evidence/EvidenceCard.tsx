import React from 'react';
import { FileText, ShieldCheck, ArrowRight, BookOpen } from 'lucide-react';
import type { ClauseCitation } from '../../types';

interface EvidenceCardProps {
  citation: ClauseCitation;
  documentName?: string;
  onJumpToDocument?: (page: number, clauseId?: string | null, quote?: string) => void;
  className?: string;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  citation,
  documentName,
  onJumpToDocument,
  className = '',
}) => {
  return (
    <div
      className={`bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:border-brand-500/50 transition-all ${className}`}
      role="region"
      aria-label={`Citation for page ${citation.page}`}
    >
      <div className="flex items-center justify-between gap-2 mb-2 pb-2 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-brand-600" aria-hidden="true" />
          <span className="text-xs font-bold text-slate-800">
            {documentName || 'Document'} &bull; Page {citation.page}
          </span>
          {citation.clause_id && (
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-brand-50 text-brand-700">
              Clause {citation.clause_id}
            </span>
          )}
        </div>

        <span
          className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200"
          title="Code-verified substring/fuzzy token overlap against stored chunk text"
        >
          <ShieldCheck className="w-3 h-3 text-emerald-600" aria-hidden="true" />
          <span>{citation.match_score ? `${Math.round(citation.match_score * 100)}% Match` : 'Verified'}</span>
        </span>
      </div>

      <div className="mb-3">
        <p className="text-xs font-mono text-slate-700 bg-slate-50 border-l-2 border-brand-500 pl-2.5 py-1.5 rounded-r italic line-clamp-4">
          &ldquo;{citation.quote}&rdquo;
        </p>
      </div>

      {onJumpToDocument && (
        <button
          onClick={() => onJumpToDocument(citation.page, citation.clause_id, citation.quote)}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-brand-600 hover:text-brand-800 focus:outline-none focus:ring-2 focus:ring-brand-500 rounded px-1.5 py-1 transition-colors"
          aria-label={`Jump to page ${citation.page} in document viewer`}
        >
          <FileText className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Jump to passage in viewer</span>
          <ArrowRight className="w-3 h-3" aria-hidden="true" />
        </button>
      )}
    </div>
  );
};
