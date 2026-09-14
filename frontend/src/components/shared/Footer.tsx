import React from 'react';
import { ShieldAlert, CheckCircle2 } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer
      className="bg-white border-t border-slate-200 py-4 px-4 sm:px-6 lg:px-8 mt-auto text-center"
      role="contentinfo"
      aria-label="Legal safety and accessibility disclaimer"
    >
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />
          <p className="text-left leading-relaxed">
            <span className="font-bold text-slate-700">Legal Safety Notice:</span> ClauseLens provides structured document analysis, not legal advice. Every factual claim is code-verified against stored lease text.
          </p>
        </div>

        <div className="flex items-center gap-3 text-[11px] text-slate-400 font-medium">
          <span className="inline-flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
            <span>WCAG AA Accessible</span>
          </span>
          <span>&bull;</span>
          <span>GenAI Legal Accessibility Challenge</span>
        </div>
      </div>
    </footer>
  );
};
