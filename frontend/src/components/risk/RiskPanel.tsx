import React, { useState } from 'react';
import { AlertTriangle, Filter, MessageSquare, PlusCircle, Check, BookOpen } from 'lucide-react';
import type { FindingItem, SeverityLevel } from '../../types';
import { StatusPill } from '../shared/StatusPill';

interface RiskPanelProps {
  findings: FindingItem[];
  onSelectCitation: (quote: string, page: number, clauseId?: string | null) => void;
  onAskAboutClause: (question: string) => void;
}

export const RiskPanel: React.FC<RiskPanelProps> = ({
  findings,
  onSelectCitation,
  onAskAboutClause,
}) => {
  const [severityFilter, setSeverityFilter] = useState<'all' | SeverityLevel>('all');
  const [addedToQuestions, setAddedToQuestions] = useState<{ [id: string]: boolean }>({});

  const filteredFindings = findings.filter((f) => {
    if (severityFilter !== 'all' && f.severity !== severityFilter) return false;
    return true;
  });

  const handleAddQuestion = (finding: FindingItem) => {
    setAddedToQuestions((prev) => ({ ...prev, [finding.id]: true }));
  };

  return (
    <div className="space-y-5 animate-fadeIn" role="region" aria-label="Risk Radar Panel">
      {/* Header & Filter Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-red-100 text-red-700">
            <AlertTriangle className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Risk Radar &bull; Identified Concerns</h2>
            <p className="text-xs text-slate-500">
              {findings.length} findings categorized by tenant legal &amp; financial exposure
            </p>
          </div>
        </div>

        {/* Severity Filter Chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs font-semibold text-slate-400 mr-1 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" aria-hidden="true" />
            Filter:
          </span>
          {(['all', 'high', 'medium', 'low'] as const).map((sev) => {
            const count = sev === 'all' ? findings.length : findings.filter((f) => f.severity === sev).length;
            const isSelected = severityFilter === sev;
            return (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-all capitalize ${
                  isSelected
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
                aria-pressed={isSelected}
              >
                {sev} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-4">
        {filteredFindings.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl border border-slate-200 text-slate-500">
            <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-slate-300" aria-hidden="true" />
            <p className="text-sm font-semibold">No findings for selected filter</p>
          </div>
        ) : (
          filteredFindings.map((f) => (
            <div
              key={f.id}
              className="bg-white rounded-xl p-5 border border-slate-200 hover:border-brand-500/40 shadow-sm transition-all"
            >
              <div className="flex flex-wrap items-start justify-between gap-3 mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-sm font-bold text-slate-900">{f.title}</h3>
                  <StatusPill severity={f.severity} />
                  <span className="text-xs text-slate-400">&bull; Page {f.page_number}</span>
                </div>
              </div>

              <p className="text-xs sm:text-sm text-slate-700 leading-relaxed mb-3">
                {f.plain_explanation}
              </p>

              {/* Verbatim Citation Excerpt */}
              {f.quote && (
                <div className="mb-4">
                  <button
                    onClick={() => onSelectCitation(f.quote!, f.page_number, f.clause_id)}
                    className="text-left w-full p-2.5 rounded-lg bg-slate-50 hover:bg-brand-50/50 border border-slate-200 hover:border-brand-300 transition-colors group"
                  >
                    <div className="flex items-center justify-between text-[11px] font-bold text-brand-700 mb-1">
                      <span className="flex items-center gap-1">
                        <BookOpen className="w-3.5 h-3.5 text-brand-600" aria-hidden="true" />
                        Verified Citation &bull; Page {f.page_number}
                      </span>
                      <span className="text-[10px] text-brand-500 group-hover:underline">
                        Click to view in document &rarr;
                      </span>
                    </div>
                    <p className="text-xs font-serif italic text-slate-800 line-clamp-3">
                      &ldquo;{f.quote}&rdquo;
                    </p>
                  </button>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-slate-100">
                <button
                  onClick={() => onAskAboutClause(`What are my rights and options regarding the clause: "${f.title}"?`)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
                >
                  <MessageSquare className="w-3.5 h-3.5" aria-hidden="true" />
                  <span>Ask Q&amp;A about this</span>
                </button>

                <button
                  onClick={() => handleAddQuestion(f)}
                  disabled={addedToQuestions[f.id]}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                    addedToQuestions[f.id]
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  {addedToQuestions[f.id] ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
                      <span>Added to Lawyer Questions</span>
                    </>
                  ) : (
                    <>
                      <PlusCircle className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
                      <span>Add to Lawyer Questions</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
