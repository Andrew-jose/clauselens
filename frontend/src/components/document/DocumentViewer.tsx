import React, { useState, useEffect, useRef } from 'react';
import { FileText, Search, Bookmark, Sparkles } from 'lucide-react';
import type { DocumentChunk, ClauseCitation } from '../../types';

interface DocumentViewerProps {
  chunks: DocumentChunk[];
  documentName?: string;
  activeCitation?: ClauseCitation | null;
  onSelectClause?: (clauseId: string, quote?: string) => void;
  className?: string;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
  chunks,
  documentName,
  activeCitation,
  onSelectClause,
  className = '',
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPage, setSelectedPage] = useState<number | 'all'>('all');
  const chunkRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  // Group chunks by page number
  const pageNumbers = Array.from(new Set(chunks.map((c) => c.page_number))).sort((a, b) => a - b);

  // Auto-scroll to matching chunk when activeCitation changes
  useEffect(() => {
    if (!activeCitation) return;

    // Find matching chunk ID
    const matchingChunk = chunks.find((c) => {
      if (activeCitation.chunk_id && c.id === activeCitation.chunk_id) return true;
      if (
        activeCitation.clause_id &&
        c.clause_id &&
        c.clause_id.toLowerCase().includes(activeCitation.clause_id.toLowerCase())
      )
        return true;
      if (activeCitation.quote && c.text.toLowerCase().includes(activeCitation.quote.toLowerCase().slice(0, 30)))
        return true;
      return false;
    });

    if (matchingChunk && chunkRefs.current[matchingChunk.id]) {
      chunkRefs.current[matchingChunk.id]?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [activeCitation, chunks]);

  // Filter chunks by search and page
  const filteredChunks = chunks.filter((c) => {
    if (selectedPage !== 'all' && c.page_number !== selectedPage) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        c.text.toLowerCase().includes(q) ||
        (c.clause_id && c.clause_id.toLowerCase().includes(q)) ||
        (c.section_heading && c.section_heading.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const isChunkActive = (chunk: DocumentChunk) => {
    if (!activeCitation) return false;
    if (activeCitation.chunk_id && chunk.id === activeCitation.chunk_id) return true;
    if (
      activeCitation.clause_id &&
      chunk.clause_id &&
      chunk.clause_id.toLowerCase().includes(activeCitation.clause_id.toLowerCase())
    )
      return true;
    if (activeCitation.quote && chunk.text.toLowerCase().includes(activeCitation.quote.toLowerCase().slice(0, 30)))
      return true;
    return false;
  };

  return (
    <div
      className={`flex flex-col h-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden ${className}`}
      role="region"
      aria-label="Document Viewer"
    >
      {/* Viewer Header / Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-brand-100 text-brand-700">
            <FileText className="w-4 h-4" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-xs font-bold text-slate-900 truncate max-w-[200px] sm:max-w-xs">
              {documentName || 'Document Text Viewer'}
            </h2>
            <p className="text-[11px] text-slate-500">
              {chunks.length} structured clauses &bull; {pageNumbers.length} pages
            </p>
          </div>
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center gap-2">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" aria-hidden="true" />
            <input
              type="text"
              placeholder="Find in lease..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1 text-xs rounded-lg border border-slate-200 bg-white text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 w-36 sm:w-44 transition-all"
              aria-label="Search within document text"
            />
          </div>

          {/* Page Filter */}
          <select
            value={selectedPage}
            onChange={(e) => setSelectedPage(e.target.value === 'all' ? 'all' : Number(e.target.value))}
            className="px-2.5 py-1 text-xs rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
            aria-label="Filter by page number"
          >
            <option value="all">All Pages ({pageNumbers.length})</option>
            {pageNumbers.map((p) => (
              <option key={p} value={p}>
                Page {p}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Document Content Pane */}
      <div
        tabIndex={0}
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 bg-slate-50/50 font-sans focus:outline-none focus:ring-2 focus:ring-inset focus:ring-brand-500"
        aria-label="Scrollable Document Content"
      >
        {filteredChunks.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <FileText className="w-8 h-8 mx-auto mb-2 text-slate-400" aria-hidden="true" />
            <p className="text-sm font-medium">No matching passages found</p>
            <p className="text-xs text-slate-400 mt-1">Try adjusting your search query or page filter.</p>
          </div>
        ) : (
          filteredChunks.map((chunk, index) => {
            const isActive = isChunkActive(chunk);
            const isFirstOnPage =
              index === 0 || filteredChunks[index - 1].page_number !== chunk.page_number;

            return (
              <React.Fragment key={chunk.id}>
                {isFirstOnPage && (
                  <div className="flex items-center gap-2 pt-4 pb-1 border-b border-slate-200">
                    <span className="text-[11px] font-extrabold uppercase tracking-wider text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                      Page {chunk.page_number}
                    </span>
                    <div className="h-px flex-1 bg-slate-200" />
                  </div>
                )}

                <div
                  ref={(el) => {
                    chunkRefs.current[chunk.id] = el;
                  }}
                  className={`relative p-4 rounded-xl transition-all duration-300 ${
                    isActive
                      ? 'bg-amber-50/90 border-2 border-brand-500 shadow-md ring-4 ring-brand-500/10'
                      : 'bg-white border border-slate-200 hover:border-slate-300 shadow-sm'
                  }`}
                >
                  {/* Clause Header & Meta */}
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      {chunk.clause_id && (
                        <span className="inline-flex items-center gap-1 text-xs font-bold text-brand-800 bg-brand-50 border border-brand-200 px-2 py-0.5 rounded">
                          <Bookmark className="w-3 h-3" aria-hidden="true" />
                          Clause {chunk.clause_id}
                        </span>
                      )}
                      {chunk.section_heading && (
                        <span className="text-xs font-semibold text-slate-700">
                          {chunk.section_heading}
                        </span>
                      )}
                    </div>

                    <span className="text-[10px] text-slate-400">
                      Page {chunk.page_number}
                    </span>
                  </div>

                  {/* Chunk Text Body */}
                  <div className="text-xs sm:text-sm text-slate-800 leading-relaxed whitespace-pre-wrap font-serif">
                    {chunk.text}
                  </div>

                  {/* Active highlight label */}
                  {isActive && (
                    <div className="mt-3 pt-2 border-t border-brand-200 flex items-center justify-between text-xs font-medium text-brand-800">
                      <span className="flex items-center gap-1">
                        <Sparkles className="w-3.5 h-3.5 text-brand-600" aria-hidden="true" />
                        Active Grounded Passage Anchor
                      </span>
                      {onSelectClause && chunk.clause_id && (
                        <button
                          onClick={() => onSelectClause(chunk.clause_id!, chunk.text)}
                          className="text-xs text-brand-600 hover:underline font-semibold"
                        >
                          Explore Clause
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </React.Fragment>
            );
          })
        )}
      </div>
    </div>
  );
};
