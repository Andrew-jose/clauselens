import React, { useState } from 'react';
import { Scale, BookOpen, Loader2 } from 'lucide-react';
import type { DocumentItem, ComparisonResponse, ClauseCitation } from '../../types';
import { StatusPill } from '../shared/StatusPill';

interface CompareViewProps {
  documents: DocumentItem[];
  currentDocId: string;
  onCompare: (docAId: string, docBId: string) => Promise<ComparisonResponse | void>;
  onSelectCitation: (citation: ClauseCitation) => void;
  isLoading?: boolean;
}

export const CompareView: React.FC<CompareViewProps> = ({
  documents,
  currentDocId,
  onCompare,
  onSelectCitation,
  isLoading = false,
}) => {
  const [docAId, setDocAId] = useState<string>(currentDocId);
  const [docBId, setDocBId] = useState<string>(
    documents.find((d) => d.id !== currentDocId)?.id || ''
  );
  const [comparisonResult, setComparisonResult] = useState<ComparisonResponse | null>(null);

  const handleRunComparison = async () => {
    if (!docAId || !docBId || docAId === docBId) return;
    const res = await onCompare(docAId, docBId);
    if (res) {
      setComparisonResult(res);
    }
  };

  const docAName = documents.find((d) => d.id === docAId)?.filename || 'Current Lease';
  const docBName = documents.find((d) => d.id === docBId)?.filename || 'Comparison Lease';

  return (
    <div className="space-y-6 animate-fadeIn" role="region" aria-label="Side-by-Side Lease Comparator">
      {/* Comparator Selector Card */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-purple-100 text-purple-700">
            <Scale className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Side-by-Side Lease Comparator</h2>
            <p className="text-xs text-slate-500">
              Cross-document comparative analysis detecting clause-level changes that favor the landlord
            </p>
          </div>
        </div>

        {/* Document Selectors */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Document A (Base Agreement)
            </label>
            <select
              value={docAId}
              onChange={(e) => setDocAId(e.target.value)}
              className="w-full p-2.5 text-xs sm:text-sm rounded-xl border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename} ({d.page_count} pages)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Document B (New Offer / Addendum)
            </label>
            <select
              value={docBId}
              onChange={(e) => setDocBId(e.target.value)}
              className="w-full p-2.5 text-xs sm:text-sm rounded-xl border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="" disabled>
                Select second document to compare...
              </option>
              {documents.map((d) => (
                <option key={d.id} value={d.id} disabled={d.id === docAId}>
                  {d.filename} {d.id === docAId ? '(Already Document A)' : ''}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={handleRunComparison}
            disabled={!docAId || !docBId || docAId === docBId || isLoading}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-purple-600 hover:bg-purple-700 text-white shadow-sm disabled:opacity-40 transition-colors"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                <span>Running Comparative Analysis...</span>
              </>
            ) : (
              <>
                <Scale className="w-4 h-4" aria-hidden="true" />
                <span>Compare Leases Clause-by-Clause</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Comparison Results */}
      {comparisonResult && (
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-purple-50 border border-purple-200 rounded-xl text-purple-950">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-purple-900 block">
                Comparative Reasoning Completed
              </span>
              <span className="text-xs text-purple-800">
                Found {comparisonResult.deltas_count} substantive differences across categorized clauses
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {comparisonResult.findings.map((finding, idx) => {
              const favorsLandlord = finding.favors === 'landlord';
              return (
                <div
                  key={idx}
                  className="bg-white rounded-2xl p-5 border border-slate-200 hover:border-purple-300 shadow-sm space-y-4 transition-all"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                        {finding.category.replace(/_/g, ' ')}
                      </span>
                      <StatusPill severity={finding.severity} />
                      <span
                        className={`text-xs font-bold px-2 py-0.5 rounded-md ${
                          favorsLandlord
                            ? 'bg-red-50 text-red-700 border border-red-200'
                            : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        }`}
                      >
                        Favors {finding.favors.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs sm:text-sm text-slate-800 font-medium leading-relaxed">
                    {finding.delta_description}
                  </p>

                  {/* Side-by-side Dual Citation Comparison */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                    {/* Document A Column */}
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block truncate">
                        {docAName}
                      </span>
                      {finding.doc_a_citation ? (
                        <div>
                          <p className="text-xs font-serif italic text-slate-800 line-clamp-3">
                            &ldquo;{finding.doc_a_citation.quote}&rdquo;
                          </p>
                          <button
                            onClick={() => onSelectCitation(finding.doc_a_citation!)}
                            className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-brand-600 hover:underline"
                          >
                            <BookOpen className="w-3 h-3" aria-hidden="true" />
                            <span>Page {finding.doc_a_citation.page}</span>
                          </button>
                        </div>
                      ) : (
                        <p className="text-xs text-slate-400 italic">No corresponding clause excerpt.</p>
                      )}
                    </div>

                    {/* Document B Column */}
                    <div className="p-3 rounded-xl bg-purple-50/50 border border-purple-200 space-y-1.5">
                      <span className="text-[11px] font-bold text-purple-700 uppercase tracking-wider block truncate">
                        {docBName}
                      </span>
                      {finding.doc_b_citation ? (
                        <div>
                          <p className="text-xs font-serif italic text-slate-800 line-clamp-3">
                            &ldquo;{finding.doc_b_citation.quote}&rdquo;
                          </p>
                          <button
                            onClick={() => onSelectCitation(finding.doc_b_citation!)}
                            className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-purple-700 hover:underline"
                          >
                            <BookOpen className="w-3 h-3" aria-hidden="true" />
                            <span>Page {finding.doc_b_citation.page}</span>
                          </button>
                        </div>
                      ) : (
                        <p className="text-xs text-slate-400 italic">No corresponding clause excerpt.</p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
