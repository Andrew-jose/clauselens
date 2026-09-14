import React, { useState } from 'react';
import {
  Compass,
  Send,
  Sparkles,
  CheckSquare,
  Square,
  AlertTriangle,
  BookOpen,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import type {
  SituationClassification,
  ActionPlanData,
  ClauseCitation,
} from '../../types';
import { StatusPill } from '../shared/StatusPill';

interface SituationPanelProps {
  situation?: SituationClassification | null;
  actionPlan?: ActionPlanData | null;
  onSubmitSituation: (contextText: string) => Promise<void>;
  onSelectCitation: (citation: ClauseCitation) => void;
  onNavigateToLawyer: () => void;
  isLoading?: boolean;
}

const PRESET_SITUATIONS = [
  {
    label: 'Relocating for work / break lease early',
    text: 'My lease ends in 6 months, but I need to move out early because my employer is relocating me to another state.',
  },
  {
    label: 'Broken heat & mold dispute',
    text: 'My landlord has refused to fix the broken heater for 2 weeks in winter and there is severe mold in the bathroom.',
  },
  {
    label: '15% rent hike on renewal offer',
    text: 'The landlord sent a renewal offer increasing monthly rent by 15% and increasing late fees.',
  },
  {
    label: 'Reviewing prospective lease before signing',
    text: 'I just received this residential lease agreement and want to review all obligations and risks before I sign.',
  },
];

export const SituationPanel: React.FC<SituationPanelProps> = ({
  situation,
  actionPlan,
  onSubmitSituation,
  onSelectCitation,
  onNavigateToLawyer,
  isLoading = false,
}) => {
  const [contextText, setContextText] = useState('');
  const [completedSteps, setCompletedSteps] = useState<{ [order: number]: boolean }>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!contextText.trim() || isLoading) return;
    await onSubmitSituation(contextText.trim());
  };

  const handlePreset = async (text: string) => {
    setContextText(text);
    await onSubmitSituation(text);
  };

  const toggleStep = (order: number) => {
    setCompletedSteps((prev) => ({ ...prev, [order]: !prev[order] }));
  };

  return (
    <div className="space-y-6 animate-fadeIn" role="region" aria-label="Situation Router and Action Plan">
      {/* Input Box Card */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-100 text-indigo-700">
            <Compass className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Situation Router &bull; Context-Aware Intelligence</h2>
            <p className="text-xs text-slate-500">
              Describe your current circumstances to reprioritize lease analysis and generate a customized action plan.
            </p>
          </div>
        </div>

        {/* Preset Chips */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-indigo-500" aria-hidden="true" />
            Preset Scenarios:
          </span>
          {PRESET_SITUATIONS.map((preset, idx) => (
            <button
              key={idx}
              onClick={() => handlePreset(preset.text)}
              disabled={isLoading}
              className="text-[11px] font-medium text-slate-700 bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 border border-slate-200 hover:border-indigo-300 rounded-lg px-2.5 py-1 transition-colors disabled:opacity-50"
            >
              {preset.label}
            </button>
          ))}
        </div>

        {/* Context Text Form */}
        <form onSubmit={handleSubmit} className="space-y-2">
          <textarea
            rows={3}
            value={contextText}
            onChange={(e) => setContextText(e.target.value)}
            placeholder="Type your situation in plain English (e.g. 'I might leave early because of a job offer,' or 'My landlord is entering without notice')..."
            className="w-full p-3 text-xs sm:text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-slate-800 placeholder-slate-400 leading-relaxed"
            aria-label="Describe your lease situation"
          />
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!contextText.trim() || isLoading}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm disabled:opacity-40 transition-colors"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  <span>Classifying &amp; Re-ranking...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" aria-hidden="true" />
                  <span>Update Situation &amp; Plan</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Dynamic Classification Banner */}
      {situation && (
        <div className="bg-gradient-to-r from-indigo-900 to-slate-900 rounded-2xl p-5 text-white shadow-sm space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="text-xs uppercase font-extrabold tracking-wider bg-white/20 px-3 py-1 rounded-full text-indigo-100">
                {situation.situation_type.replace(/_/g, ' ')}
              </span>
              <StatusPill severity={situation.urgency} />
            </div>

            <span className="text-xs text-indigo-200">
              Downstream retrieval re-ranked by {situation.relevant_categories.length} priority categories
            </span>
          </div>

          <div className="flex items-center gap-2 flex-wrap pt-2 border-t border-white/10">
            <span className="text-[11px] font-bold text-indigo-200 uppercase tracking-wider">
              Relevant Clause Categories:
            </span>
            {situation.relevant_categories.map((cat, i) => (
              <span
                key={i}
                className="text-xs font-medium bg-white/10 px-2.5 py-0.5 rounded-md border border-white/15 text-white"
              >
                {cat.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Action Plan Stepper / Checklist */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Recommended Action Plan Checklist</h3>
            <p className="text-xs text-slate-500">
              Ordered, concrete next steps tailored to your classified situation and lease findings
            </p>
          </div>

          <button
            onClick={onNavigateToLawyer}
            className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-800"
          >
            <span>Proceed to Lawyer Prep</span>
            <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>

        {/* High Urgency Consultation Alert */}
        {situation && (situation.situation_type === 'active_dispute' || situation.urgency === 'high') && (
          <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-950 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="text-xs leading-relaxed">
              <span className="font-bold text-red-900 block mb-0.5">High Urgency Situation Detected</span>
              Because this scenario involves an active dispute or significant financial exposure, seeking professional legal assistance from a local tenant union or attorney is strongly recommended before taking unilateral action.
            </div>
          </div>
        )}

        {/* Steps List */}
        {!actionPlan || actionPlan.steps.length === 0 ? (
          <p className="text-xs text-slate-500 py-6 text-center">
            Submit your situation above to generate a customized step-by-step action plan.
          </p>
        ) : (
          <div className="space-y-3">
            {actionPlan.steps.map((step) => {
              const isDone = completedSteps[step.order];
              return (
                <div
                  key={step.order}
                  className={`p-4 rounded-xl border transition-all ${
                    isDone
                      ? 'bg-slate-50/70 border-slate-200 opacity-75'
                      : 'bg-white border-slate-200 hover:border-indigo-300 shadow-2xs'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <button
                      onClick={() => toggleStep(step.order)}
                      className="mt-0.5 text-slate-400 hover:text-indigo-600 focus:outline-none"
                      aria-label={`Mark step ${step.order} as ${isDone ? 'incomplete' : 'complete'}`}
                    >
                      {isDone ? (
                        <CheckSquare className="w-4 h-4 text-emerald-600" aria-hidden="true" />
                      ) : (
                        <Square className="w-4 h-4" aria-hidden="true" />
                      )}
                    </button>

                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900">
                          Step {step.order}: {step.action}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {step.rationale}
                      </p>

                      {step.citation && (
                        <button
                          onClick={() => onSelectCitation(step.citation!)}
                          className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-brand-700 hover:text-brand-900 bg-brand-50 hover:bg-brand-100/70 px-2 py-0.5 rounded border border-brand-200 transition-colors"
                        >
                          <BookOpen className="w-3 h-3" aria-hidden="true" />
                          <span>
                            Cited Document Anchor &bull; Page {step.citation.page}
                            {step.citation.clause_id ? ` (Clause ${step.citation.clause_id})` : ''}
                          </span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
