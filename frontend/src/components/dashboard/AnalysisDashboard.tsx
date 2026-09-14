import React from 'react';
import {
  FileText,
  AlertTriangle,
  ShieldCheck,
  Compass,
  MessageSquare,
  Scale,
  ArrowRight,
  BookOpen,
  Sparkles,
  Download,
} from 'lucide-react';
import type { DocumentItem, FindingItem, ClauseItem } from '../../types';
import { StatusPill } from '../shared/StatusPill';

interface AnalysisDashboardProps {
  document: DocumentItem;
  findings: FindingItem[];
  clauses: ClauseItem[];
  onNavigate: (tab: string) => void;
  onSelectFindingCitation?: (quote: string, page: number, clauseId?: string | null) => void;
}

export const AnalysisDashboard: React.FC<AnalysisDashboardProps> = ({
  document,
  findings,
  clauses,
  onNavigate,
  onSelectFindingCitation,
}) => {
  const highRiskCount = findings.filter((f) => f.severity === 'high').length;

  return (
    <div className="space-y-6 animate-fadeIn" role="region" aria-label="Lease Analysis Dashboard">
      {/* Top Banner / Document Title Card */}
      <div className="bg-gradient-to-r from-brand-900 via-brand-700 to-brand-600 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
        <div className="absolute -right-8 -top-8 w-40 h-40 bg-white/10 rounded-full blur-2xl pointer-events-none" />

        <div className="flex flex-wrap items-start justify-between gap-4 relative z-10">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-white/15 text-brand-100 border border-white/20 mb-3">
              <Sparkles className="w-3.5 h-3.5 text-yellow-300" aria-hidden="true" />
              <span>Evidence-Grounding Active</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
              {document.filename}
            </h1>
            <p className="text-xs sm:text-sm text-brand-100/90 mt-1">
              Residential Lease Agreement &bull; {document.page_count} Pages &bull; {clauses.length} Clauses Indexed
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onNavigate('ask')}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-white text-brand-700 hover:bg-brand-50 shadow-sm focus:outline-none focus:ring-2 focus:ring-white transition-all"
            >
              <MessageSquare className="w-4 h-4" aria-hidden="true" />
              <span>Ask Document</span>
            </button>
            <button
              onClick={() => onNavigate('lawyer')}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-white/15 text-white hover:bg-white/25 border border-white/20 focus:outline-none focus:ring-2 focus:ring-white transition-all"
            >
              <Download className="w-4 h-4" aria-hidden="true" />
              <span>Lawyer Packet</span>
            </button>
          </div>
        </div>

        {/* Identified Key Terms */}
        {document.key_terms && document.key_terms.length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/15 flex items-center gap-2 flex-wrap">
            <span className="text-[11px] uppercase font-bold text-brand-200 tracking-wider">
              Key Identified Terms:
            </span>
            {document.key_terms.map((term, i) => (
              <span
                key={i}
                className="text-xs font-medium bg-white/10 px-2.5 py-0.5 rounded-full border border-white/15 text-white"
              >
                {term}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 3 Quick Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 rounded-xl bg-brand-50 text-brand-600">
            <BookOpen className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900">{clauses.length}</div>
            <div className="text-xs font-semibold text-slate-500">Structured Clauses</div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 rounded-xl bg-red-50 text-red-600">
            <AlertTriangle className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <div className="text-2xl font-black text-red-600">{highRiskCount}</div>
            <div className="text-xs font-semibold text-slate-500">High Severity Risks</div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 rounded-xl bg-emerald-50 text-emerald-600">
            <ShieldCheck className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <div className="text-2xl font-black text-emerald-600">{findings.length}</div>
            <div className="text-xs font-semibold text-slate-500">Verified Findings</div>
          </div>
        </div>
      </div>

      {/* Executive Summary & Top Findings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Executive Summary */}
        <div className="lg:col-span-5 bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="p-1.5 rounded-lg bg-brand-100 text-brand-700">
                <FileText className="w-4 h-4" aria-hidden="true" />
              </div>
              <h2 className="text-sm font-bold text-slate-900">Executive Lease Summary</h2>
            </div>
            <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
              {document.summary ||
                'This residential lease agreement sets forth tenant financial obligations, security deposit conditions, maintenance responsibilities, and early termination provisions. All clauses are indexed with verbatim evidence quotes.'}
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100">
            <button
              onClick={() => onNavigate('viewer')}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-brand-600 hover:text-brand-800"
            >
              <span>View full lease in Document Viewer</span>
              <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          </div>
        </div>

        {/* Risk Radar Preview: Top 3 Findings */}
        <div className="lg:col-span-7 bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-red-100 text-red-700">
                <AlertTriangle className="w-4 h-4" aria-hidden="true" />
              </div>
              <h2 className="text-sm font-bold text-slate-900">Risk Radar &bull; Top Concerns</h2>
            </div>
            <button
              onClick={() => onNavigate('risk')}
              className="text-xs font-semibold text-brand-600 hover:text-brand-800 flex items-center gap-1"
            >
              <span>See all ({findings.length})</span>
              <ArrowRight className="w-3 h-3" aria-hidden="true" />
            </button>
          </div>

          {findings.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">
              No problematic clauses detected in this document.
            </p>
          ) : (
            <div className="space-y-3">
              {findings.slice(0, 3).map((f) => (
                <div
                  key={f.id}
                  className="p-3.5 rounded-xl border border-slate-200 hover:border-brand-500/40 bg-slate-50/50 transition-all"
                >
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <h3 className="text-xs font-bold text-slate-900">{f.title}</h3>
                    <StatusPill severity={f.severity} />
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed mb-2">
                    {f.plain_explanation}
                  </p>
                  {f.quote && (
                    <button
                      onClick={() =>
                        onSelectFindingCitation &&
                        onSelectFindingCitation(f.quote!, f.page_number, f.clause_id)
                      }
                      className="text-[11px] font-medium text-brand-700 hover:text-brand-900 hover:underline flex items-center gap-1"
                    >
                      <BookOpen className="w-3 h-3" aria-hidden="true" />
                      <span>
                        Page {f.page_number} &bull; &ldquo;{f.quote.slice(0, 60)}...&rdquo;
                      </span>
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Module Navigation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <button
          onClick={() => onNavigate('situation')}
          className="text-left p-4 rounded-xl border border-slate-200 bg-white hover:border-brand-500 hover:shadow-sm transition-all group"
        >
          <div className="p-2 w-fit rounded-lg bg-indigo-50 text-indigo-700 mb-2 group-hover:scale-105 transition-transform">
            <Compass className="w-5 h-5" aria-hidden="true" />
          </div>
          <h3 className="text-xs font-bold text-slate-900">Situation Router</h3>
          <p className="text-[11px] text-slate-500 mt-1">
            State your scenario (e.g. relocate, dispute) to get dynamic priority and action plan.
          </p>
        </button>

        <button
          onClick={() => onNavigate('clauses')}
          className="text-left p-4 rounded-xl border border-slate-200 bg-white hover:border-brand-500 hover:shadow-sm transition-all group"
        >
          <div className="p-2 w-fit rounded-lg bg-blue-50 text-blue-700 mb-2 group-hover:scale-105 transition-transform">
            <BookOpen className="w-5 h-5" aria-hidden="true" />
          </div>
          <h3 className="text-xs font-bold text-slate-900">Clause Explorer</h3>
          <p className="text-[11px] text-slate-500 mt-1">
            Browse categorized lease clauses with plain-English tenant impact summaries.
          </p>
        </button>

        <button
          onClick={() => onNavigate('compare')}
          className="text-left p-4 rounded-xl border border-slate-200 bg-white hover:border-brand-500 hover:shadow-sm transition-all group"
        >
          <div className="p-2 w-fit rounded-lg bg-purple-50 text-purple-700 mb-2 group-hover:scale-105 transition-transform">
            <Scale className="w-5 h-5" aria-hidden="true" />
          </div>
          <h3 className="text-xs font-bold text-slate-900">Lease Comparator</h3>
          <p className="text-[11px] text-slate-500 mt-1">
            Side-by-side diff between current lease and renewal offer with severity flagging.
          </p>
        </button>

        <button
          onClick={() => onNavigate('lawyer')}
          className="text-left p-4 rounded-xl border border-slate-200 bg-white hover:border-brand-500 hover:shadow-sm transition-all group"
        >
          <div className="p-2 w-fit rounded-lg bg-emerald-50 text-emerald-700 mb-2 group-hover:scale-105 transition-transform">
            <Download className="w-5 h-5" aria-hidden="true" />
          </div>
          <h3 className="text-xs font-bold text-slate-900">Lawyer Consultation Packet</h3>
          <p className="text-[11px] text-slate-500 mt-1">
            Export a branded PDF packet with summary, risks, action plan, and counsel questions.
          </p>
        </button>
      </div>
    </div>
  );
};
