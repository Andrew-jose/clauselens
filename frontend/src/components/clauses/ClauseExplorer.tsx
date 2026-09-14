import React, { useState } from 'react';
import { BookOpen, Filter, ArrowRight, Bookmark } from 'lucide-react';
import type { ClauseItem, ClauseCategory } from '../../types';

interface ClauseExplorerProps {
  clauses: ClauseItem[];
  onSelectClause: (clauseId: string, quote?: string, page?: number) => void;
}

const CATEGORY_LABELS: { [key in ClauseCategory]?: string } = {
  rent_fees: 'Rent & Fees',
  term_renewal: 'Term & Renewal',
  termination_penalties: 'Termination & Penalties',
  repairs_habitability: 'Repairs & Habitability',
  access_privacy: 'Access & Privacy',
  deposit: 'Security Deposit',
  restrictions: 'Rules & Restrictions',
  other: 'General Terms',
};

export const ClauseExplorer: React.FC<ClauseExplorerProps> = ({ clauses, onSelectClause }) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const categories = Array.from(new Set(clauses.map((c) => c.category)));

  const filteredClauses = clauses.filter((c) => {
    if (selectedCategory !== 'all' && c.category !== selectedCategory) return false;
    return true;
  });

  return (
    <div className="space-y-5 animate-fadeIn" role="region" aria-label="Clause Explorer">
      {/* Header & Category Filter */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-blue-100 text-blue-700">
            <BookOpen className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Clause Explorer</h2>
            <p className="text-xs text-slate-500">
              Categorized breakdown of all {clauses.length} clauses detected in your lease
            </p>
          </div>
        </div>

        {/* Category Filter Chips */}
        <div className="flex items-center gap-1.5 flex-wrap pt-2 border-t border-slate-100">
          <span className="text-xs font-semibold text-slate-400 mr-1 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" aria-hidden="true" />
            Category:
          </span>
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-2.5 py-1 text-xs font-bold rounded-lg transition-all ${
              selectedCategory === 'all'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
            aria-pressed={selectedCategory === 'all'}
          >
            All ({clauses.length})
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 text-xs font-bold rounded-lg transition-all ${
                selectedCategory === cat
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
              aria-pressed={selectedCategory === cat}
            >
              {CATEGORY_LABELS[cat] || cat} ({clauses.filter((c) => c.category === cat).length})
            </button>
          ))}
        </div>
      </div>

      {/* Clauses Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredClauses.map((clause) => (
          <div
            key={clause.id}
            className="bg-white rounded-xl p-5 border border-slate-200 hover:border-brand-500/40 shadow-sm flex flex-col justify-between transition-all"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="inline-flex items-center gap-1 text-xs font-bold text-brand-800 bg-brand-50 border border-brand-200 px-2.5 py-0.5 rounded-md">
                  <Bookmark className="w-3 h-3" aria-hidden="true" />
                  Clause {clause.clause_number || 'N/A'}
                </span>
                <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                  {CATEGORY_LABELS[clause.category] || clause.category}
                </span>
              </div>

              {clause.heading && (
                <h3 className="text-sm font-bold text-slate-900 mb-1.5">{clause.heading}</h3>
              )}

              {clause.summary && (
                <p className="text-xs text-slate-700 leading-relaxed mb-3">
                  {clause.summary}
                </p>
              )}

              {clause.quote && (
                <div className="p-2.5 rounded-lg bg-slate-50 border-l-2 border-brand-500 font-serif text-xs italic text-slate-800 line-clamp-3 mb-3">
                  &ldquo;{clause.quote}&rdquo;
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">Page {clause.page_number}</span>
              <button
                onClick={() =>
                  onSelectClause(clause.clause_number || clause.id, clause.quote || undefined, clause.page_number)
                }
                className="inline-flex items-center gap-1 text-xs font-bold text-brand-600 hover:text-brand-800"
              >
                <span>Locate in Document</span>
                <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
