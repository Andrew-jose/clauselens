import React from 'react';
import {
  ShieldCheck,
  AlertCircle,
  FileX,
  Info,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';
import type { GroundedStatus, SeverityLevel } from '../../types';

interface StatusPillProps {
  status?: GroundedStatus;
  severity?: SeverityLevel;
  className?: string;
}

export const StatusPill: React.FC<StatusPillProps> = ({ status, severity, className = '' }) => {
  if (status) {
    switch (status) {
      case 'grounded_high':
        return (
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 ${className}`}
            role="status"
            aria-label="Status: Grounded with high confidence"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
            <span>Grounded</span>
          </span>
        );
      case 'grounded_low':
        return (
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200 ${className}`}
            role="status"
            aria-label="Status: Grounded with inferential confidence"
          >
            <AlertCircle className="w-3.5 h-3.5 text-amber-600" aria-hidden="true" />
            <span>Inferential</span>
          </span>
        );
      case 'not_found_in_document':
        return (
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300 ${className}`}
            role="status"
            aria-label="Status: Not found in document"
          >
            <FileX className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
            <span>Not in Document</span>
          </span>
        );
      case 'general_info':
        return (
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 ${className}`}
            role="status"
            aria-label="Status: General information"
          >
            <Info className="w-3.5 h-3.5 text-blue-600" aria-hidden="true" />
            <span>General Info</span>
          </span>
        );
    }
  }

  if (severity) {
    switch (severity) {
      case 'high':
        return (
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200 ${className}`}
            role="status"
            aria-label="Severity: High risk"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-red-600" aria-hidden="true" />
            <span>High Risk</span>
          </span>
        );
      case 'medium':
        return (
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 ${className}`}
            role="status"
            aria-label="Severity: Medium risk"
          >
            <AlertCircle className="w-3.5 h-3.5 text-amber-600" aria-hidden="true" />
            <span>Medium Risk</span>
          </span>
        );
      case 'low':
        return (
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200 ${className}`}
            role="status"
            aria-label="Severity: Low risk"
          >
            <CheckCircle className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
            <span>Low Risk</span>
          </span>
        );
    }
  }

  return null;
};
