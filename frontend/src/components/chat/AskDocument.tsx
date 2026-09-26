import React, { useState } from 'react';
import { Send, MessageSquare, Sparkles, BookOpen, ShieldCheck, Loader2 } from 'lucide-react';
import type { MessageItem, ClauseCitation } from '../../types';
import { StatusPill } from '../shared/StatusPill';

interface AskDocumentProps {
  messages: MessageItem[];
  onSendMessage: (question: string) => Promise<void>;
  onSelectCitation: (citation: ClauseCitation) => void;
  isLoading?: boolean;
}

const PRESET_PROMPTS = [
  'How much notice do I have to give before moving out?',
  'What is the financial penalty if I break this lease early?',
  'Is 60 days notice legal in my state?',
];

export const AskDocument: React.FC<AskDocumentProps> = ({
  messages,
  onSendMessage,
  onSelectCitation,
  isLoading = false,
}) => {
  const [inputQuery, setInputQuery] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isLoading) return;
    const q = inputQuery.trim();
    setInputQuery('');
    await onSendMessage(q);
  };

  const handlePresetClick = async (preset: string) => {
    if (isLoading) return;
    await onSendMessage(preset);
  };

  return (
    <div
      className="flex flex-col h-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
      role="region"
      aria-label="Evidence-Grounded Q&A Assistant"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-brand-100 text-brand-700">
            <MessageSquare className="w-4 h-4" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-xs font-bold text-slate-900">Ask Document &bull; Grounded Q&amp;A</h2>
            <p className="text-[11px] text-slate-500">Every claim is code-verified against source lease clauses</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
          <span>Anti-Hallucination Active</span>
        </div>
      </div>

      {/* Suggested Quick Prompts */}
      <div className="px-5 py-2.5 bg-slate-50/50 border-b border-slate-100 flex items-center gap-2 overflow-x-auto">
        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider whitespace-nowrap flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-yellow-500" aria-hidden="true" />
          Suggested:
        </span>
        {PRESET_PROMPTS.map((preset, idx) => (
          <button
            key={idx}
            onClick={() => handlePresetClick(preset)}
            disabled={isLoading}
            className="text-[11px] font-medium text-slate-700 bg-white hover:bg-brand-50 hover:text-brand-700 border border-slate-200 hover:border-brand-300 rounded-lg px-2.5 py-1 whitespace-nowrap transition-colors disabled:opacity-50"
          >
            {preset}
          </button>
        ))}
      </div>

      {/* Message List */}
      <div
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 font-sans"
        aria-live="polite"
        aria-atomic="false"
        role="log"
        aria-label="Conversation message history"
      >
        {messages.length === 0 ? (
          <div className="text-center py-12 text-slate-500 max-w-md mx-auto">
            <div className="w-10 h-10 rounded-full bg-brand-50 text-brand-600 flex items-center justify-center mx-auto mb-3">
              <MessageSquare className="w-5 h-5" aria-hidden="true" />
            </div>
            <h3 className="text-sm font-bold text-slate-800">Ask any question about your lease</h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              ClauseLens retrieves the relevant clauses, extracts the exact terms, and verifies citations in code before answering. Try clicking a suggested prompt above!
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              {msg.role === 'user' ? (
                <div className="max-w-[85%] sm:max-w-[70%] bg-brand-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-xs sm:text-sm font-medium shadow-sm">
                  {msg.content}
                </div>
              ) : (
                <div className="max-w-[90%] sm:max-w-[85%] bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-sm p-4 text-xs sm:text-sm text-slate-800 shadow-sm space-y-3">
                  {/* Status & Grounding Header */}
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <StatusPill status={msg.status} />
                    {msg.citations && msg.citations.length > 0 && (
                      <span className="text-[11px] text-slate-500 font-medium">
                        {msg.citations.length} Verified Citation{msg.citations.length > 1 ? 's' : ''}
                      </span>
                    )}
                  </div>

                  {/* Answer Text */}
                  <div className="text-slate-800 leading-relaxed font-sans whitespace-pre-wrap">
                    {msg.content}
                  </div>

                  {/* Clickable Citation Chips */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="pt-2 border-t border-slate-200">
                      <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                        Evidence Citations (click to inspect):
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {msg.citations.map((cit, idx) => (
                          <button
                            key={idx}
                            onClick={() => onSelectCitation(cit)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-lg bg-white border border-slate-200 hover:border-brand-500 hover:bg-brand-50/50 text-brand-700 shadow-2xs transition-all group"
                          >
                            <BookOpen className="w-3.5 h-3.5 text-brand-600" aria-hidden="true" />
                            <span>
                              Page {cit.page}
                              {cit.clause_id ? ` &bull; Clause ${cit.clause_id}` : ''}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Confidence Note */}
                  {msg.confidence_note && (
                    <p className="text-[11px] text-slate-500 italic pt-1">
                      {msg.confidence_note}
                    </p>
                  )}
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div
            className="flex items-center gap-2 text-xs font-semibold text-slate-500 bg-slate-50 p-3 rounded-xl w-fit"
            role="status"
            aria-live="polite"
          >
            <Loader2 className="w-4 h-4 animate-spin text-brand-600" aria-hidden="true" />
            <span>Retrieving chunks &amp; verifying citations...</span>
          </div>
        )}
      </div>

      {/* Input Box */}
      <form onSubmit={handleSubmit} className="p-3 sm:p-4 bg-slate-50 border-t border-slate-200">
        <div className="relative flex items-center">
          <input
            type="text"
            placeholder="Ask anything about this lease agreement..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isLoading}
            className="w-full pl-4 pr-12 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-300 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 shadow-sm"
            aria-label="Ask a question about the lease document"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isLoading}
            className="absolute right-1.5 p-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white disabled:opacity-40 disabled:hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
            aria-label="Send question"
          >
            <Send className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
      </form>
    </div>
  );
};
