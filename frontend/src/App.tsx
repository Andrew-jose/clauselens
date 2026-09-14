import { useEffect, useState } from 'react';
import { checkHealth, checkGeminiHealth } from './api/client';
import type { HealthResponse, GeminiHealthResponse } from './api/client';
import { ShieldCheck, FileText, CheckCircle2, AlertCircle, ArrowRight, BookOpen, Scale, Sparkles } from 'lucide-react';

export function App() {
  const [backendHealth, setBackendHealth] = useState<HealthResponse | null>(null);
  const [geminiHealth, setGeminiHealth] = useState<GeminiHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStatus() {
      try {
        const [health, gemini] = await Promise.allSettled([
          checkHealth(),
          checkGeminiHealth(),
        ]);
        if (health.status === 'fulfilled') setBackendHealth(health.value);
        if (gemini.status === 'fulfilled') setGeminiHealth(gemini.value);
      } catch (e) {
        console.error('Failed checking health:', e);
      } finally {
        setLoading(false);
      }
    }
    loadStatus();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      {/* Navigation */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-brand-500 text-white p-2 rounded-lg shadow-sm">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-slate-900">ClauseLens</span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded bg-blue-100 text-brand-700">Tenant Edition</span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3 text-xs">
              <div className="flex items-center space-x-1.5">
                <span className="text-slate-500">API:</span>
                {loading ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 animate-pulse">
                    Checking...
                  </span>
                ) : backendHealth?.status === 'ok' ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                    <CheckCircle2 className="w-3 h-3 mr-1" /> Ready
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                    <AlertCircle className="w-3 h-3 mr-1" /> Offline
                  </span>
                )}
              </div>

              <div className="flex items-center space-x-1.5">
                <span className="text-slate-500">AI:</span>
                {loading ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 animate-pulse">
                    Checking...
                  </span>
                ) : geminiHealth?.status === 'ok' ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                    <Sparkles className="w-3 h-3 mr-1" /> Gemini Ready
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-brand-700">
                    <Sparkles className="w-3 h-3 mr-1" /> {geminiHealth?.flash_model || 'gemini-3.8-flash'}
                  </span>
                )}
              </div>
            </div>

            <button className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-brand-500 hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 transition-colors">
              Upload Lease
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-brand-600 border border-blue-200 mb-6">
            <Scale className="w-3.5 h-3.5 mr-1.5" /> Evidence-First Tenancy Assistant
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight mb-4">
            Every claim, traced to the clause it came from.
          </h1>
          <p className="text-lg text-slate-600 mb-8 leading-relaxed">
            ClauseLens turns your dense residential lease into an evidence-verified map of your rights, risks, and next steps. Powered by code-level citation validation so you never receive an ungrounded claim.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-brand-500 hover:bg-brand-600 transition-all">
              <FileText className="w-5 h-5 mr-2" /> Upload Your Lease (PDF / DOCX)
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
            <button className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 border border-slate-300 text-base font-medium rounded-lg text-slate-700 bg-white hover:bg-slate-50 transition-all">
              <BookOpen className="w-5 h-5 mr-2 text-slate-500" /> View Demo Lease
            </button>
          </div>
        </div>

        {/* 3 Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow transition-shadow">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Code-Verified Citations</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Every factual finding links directly to a verified excerpt in your uploaded document. Unsupported hallucinations are structurally blocked in code.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow transition-shadow">
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-brand-600 flex items-center justify-center mb-4">
              <Scale className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Dynamic Situation Router</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Share your scenario (e.g. early job relocation, security deposit dispute) and watch risk prioritization adapt specifically to your tenant context.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow transition-shadow">
            <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center mb-4">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Lawyer-Prep Packet</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Generate an organized, clause-referenced briefing packet with prioritized questions ready for a tenant clinic or consultation.
            </p>
          </div>
        </div>
      </main>

      {/* Persistent Legal Disclaimer Footer */}
      <footer className="border-t border-slate-200 bg-white py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© 2026 ClauseLens. Built for the GenAI Legal Accessibility Challenge.</p>
          <p className="font-medium text-slate-600">
            ClauseLens provides information, not legal advice.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
