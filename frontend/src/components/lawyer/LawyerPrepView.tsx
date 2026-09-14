import React, { useState } from 'react';
import { Download, FileText, CheckSquare, Square, Plus, ShieldCheck } from 'lucide-react';
import type { LawyerQuestionsData, LawyerQuestionItem, DocumentItem } from '../../types';
import { StatusPill } from '../shared/StatusPill';

interface LawyerPrepViewProps {
  document: DocumentItem;
  questionsData?: LawyerQuestionsData | null;
  exportPdfUrl: string;
}

export const LawyerPrepView: React.FC<LawyerPrepViewProps> = ({
  document,
  questionsData,
  exportPdfUrl,
}) => {
  const [checkedQuestions, setCheckedQuestions] = useState<{ [id: number]: boolean }>({});
  const [customQuestion, setCustomQuestion] = useState('');
  const [localQuestions, setLocalQuestions] = useState<LawyerQuestionItem[]>(
    questionsData?.questions || []
  );

  React.useEffect(() => {
    if (questionsData?.questions) {
      setLocalQuestions(questionsData.questions);
    }
  }, [questionsData]);

  const toggleCheck = (idx: number) => {
    setCheckedQuestions((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const handleAddCustom = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customQuestion.trim()) return;
    setLocalQuestions((prev) => [
      ...prev,
      {
        topic: 'Custom Question',
        question: customQuestion.trim(),
        priority: 'medium',
      },
    ]);
    setCustomQuestion('');
  };

  return (
    <div className="space-y-6 animate-fadeIn" role="region" aria-label="Lawyer Consultation Preparation">
      {/* Top Action Card */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="p-1.5 rounded-lg bg-emerald-100 text-emerald-700">
              <FileText className="w-5 h-5" aria-hidden="true" />
            </div>
            <h2 className="text-sm font-bold text-slate-900">Lawyer Consultation Preparation Packet</h2>
          </div>
          <p className="text-xs text-slate-500">
            Export a comprehensive, page-and-clause-cited brief for your 15-minute consult or legal clinic
          </p>
        </div>

        <a
          href={exportPdfUrl}
          download={`lawyer_prep_${document.id.slice(0, 8)}.pdf`}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-colors"
        >
          <Download className="w-4 h-4" aria-hidden="true" />
          <span>Download PDF Consultation Packet</span>
        </a>
      </div>

      {/* Packet Preview Box */}
      <div className="bg-slate-50 rounded-2xl p-5 border border-slate-200 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 pb-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Targeted Questions for Legal Counsel ({localQuestions.length})
          </h3>
          <span className="text-xs text-slate-500 font-medium">
            Prioritized by high-severity findings &bull; Fabricated statutes guarded
          </span>
        </div>

        {/* Questions List */}
        {localQuestions.length === 0 ? (
          <p className="text-xs text-slate-500 py-6 text-center">
            No specific legal questions generated yet.
          </p>
        ) : (
          <div className="space-y-3">
            {localQuestions.map((q, idx) => {
              const isChecked = checkedQuestions[idx];
              return (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border transition-all ${
                    isChecked
                      ? 'bg-slate-100/70 border-slate-200 opacity-60'
                      : 'bg-white border-slate-200 hover:border-emerald-300 shadow-2xs'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <button
                      onClick={() => toggleCheck(idx)}
                      className="mt-0.5 text-slate-400 hover:text-emerald-600 focus:outline-none"
                      aria-label={`Mark question ${idx + 1} as ${isChecked ? 'unasked' : 'asked'}`}
                    >
                      {isChecked ? (
                        <CheckSquare className="w-4 h-4 text-emerald-600" aria-hidden="true" />
                      ) : (
                        <Square className="w-4 h-4" aria-hidden="true" />
                      )}
                    </button>

                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-bold text-slate-800">
                          {q.topic}
                        </span>
                        <StatusPill severity={q.priority} />
                      </div>
                      <p className="text-xs sm:text-sm text-slate-800 leading-relaxed font-sans">
                        {q.question}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Add Custom Question Form */}
        <form onSubmit={handleAddCustom} className="pt-3 border-t border-slate-200 flex gap-2">
          <input
            type="text"
            placeholder="Add your own custom question for counsel..."
            value={customQuestion}
            onChange={(e) => setCustomQuestion(e.target.value)}
            className="flex-1 px-3 py-2 text-xs rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            aria-label="Add custom question"
          />
          <button
            type="submit"
            disabled={!customQuestion.trim()}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-xl bg-slate-800 hover:bg-slate-900 text-white disabled:opacity-40 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Add</span>
          </button>
        </form>
      </div>

      {/* Responsible-AI Disclaimer Banner */}
      <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-slate-600 flex items-start gap-2 text-xs leading-relaxed">
        <ShieldCheck className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <span className="font-bold text-slate-800">Legal Safety &amp; Non-Advice Policy:</span> ClauseLens provides structured information, clause maps, and risk radar analysis, not legal advice. The exported PDF preparation packet is designed exclusively to facilitate informed consultations with a licensed attorney or housing clinic.
        </div>
      </div>
    </div>
  );
};
