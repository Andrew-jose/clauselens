import React from 'react';
import {
  FileText,
  Upload,
  Layers,
  AlertTriangle,
  BookOpen,
  MessageSquare,
  Compass,
  Scale,
  Download,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import type { DocumentItem } from '../../types';

interface HeaderProps {
  documents: DocumentItem[];
  selectedDocumentId?: string;
  onSelectDocument: (id: string) => void;
  onOpenUploadModal: () => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
  apiConnected: boolean;
  geminiConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  documents,
  selectedDocumentId,
  onSelectDocument,
  onOpenUploadModal,
  activeTab,
  onTabChange,
  apiConnected,
  geminiConnected,
}) => {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Layers },
    { id: 'viewer', label: 'Document Viewer', icon: FileText },
    { id: 'risk', label: 'Risk Radar', icon: AlertTriangle },
    { id: 'clauses', label: 'Clause Explorer', icon: BookOpen },
    { id: 'ask', label: 'Ask Document', icon: MessageSquare },
    { id: 'situation', label: 'Situation & Plan', icon: Compass },
    { id: 'compare', label: 'Compare', icon: Scale },
    { id: 'lawyer', label: 'Lawyer Prep', icon: Download },
  ];

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200 shadow-2xs">
      {/* Top Navbar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Brand Logo & Tagline */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-brand-600 text-white flex items-center justify-center shadow-md">
              <FileText className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <span className="text-lg font-black tracking-tight text-slate-900 block leading-none">
                Clause<span className="text-brand-600">Lens</span>
              </span>
              <span className="text-[10px] text-slate-500 font-medium hidden sm:block">
                Every claim, traced to the clause it came from.
              </span>
            </div>
          </div>

          {/* Document Switcher & Upload */}
          <div className="flex items-center gap-2 sm:gap-3">
            {documents.length > 0 && (
              <select
                value={selectedDocumentId}
                onChange={(e) => onSelectDocument(e.target.value)}
                className="max-w-[160px] sm:max-w-xs px-3 py-1.5 text-xs font-semibold rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 truncate"
                aria-label="Active Document Selector"
              >
                {documents.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.filename} ({d.page_count}p)
                  </option>
                ))}
              </select>
            )}

            <button
              onClick={onOpenUploadModal}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-xl bg-brand-600 hover:bg-brand-700 text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
              aria-label="Upload New Lease"
            >
              <Upload className="w-3.5 h-3.5" aria-hidden="true" />
              <span className="hidden sm:inline">Upload Lease</span>
            </button>

            {/* Health Signals */}
            <div className="hidden md:flex items-center gap-2 pl-2 border-l border-slate-200 text-[11px] font-semibold text-slate-600">
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${
                  apiConnected
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}
              >
                <Activity className="w-3 h-3" aria-hidden="true" />
                <span>API: {apiConnected ? 'Online' : 'Offline'}</span>
              </span>

              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${
                  geminiConnected
                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                }`}
              >
                <CheckCircle2 className="w-3 h-3" aria-hidden="true" />
                <span>Gemini: {geminiConnected ? 'Active' : 'Offline/Mock'}</span>
              </span>
            </div>
          </div>
        </div>

        {/* Tab Navigation Bar */}
        <nav
          className="flex space-x-1 overflow-x-auto pb-1 scrollbar-none"
          aria-label="Application Sections"
        >
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`inline-flex items-center gap-2 px-3.5 py-2 text-xs font-bold border-b-2 whitespace-nowrap transition-all ${
                  isActive
                    ? 'border-brand-600 text-brand-700 bg-brand-50/50'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                }`}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="w-4 h-4" aria-hidden="true" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
