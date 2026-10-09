'use client';

import React, { useState } from "react";
import { SourceCitation } from "../lib/types";
import { BookOpen, ChevronDown, ChevronUp, FileText } from "lucide-react";

interface SourceCitationProps {
  sources: SourceCitation[];
}

export const SourceCitationsList: React.FC<SourceCitationProps> = ({ sources }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-800">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
        <BookOpen className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
        <span>Verified Handbook Evidence ({sources.length})</span>
      </div>
      <div className="grid grid-cols-1 gap-2">
        {sources.map((src, idx) => {
          const isExpanded = expandedIndex === idx;
          return (
            <div
              key={idx}
              className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 p-2.5 text-xs transition-colors hover:border-indigo-300 dark:hover:border-indigo-800"
            >
              <button
                type="button"
                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                className="w-full flex items-center justify-between text-left font-medium text-slate-700 dark:text-slate-200"
              >
                <div className="flex items-center gap-2 truncate">
                  <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span className="truncate">{src.document}</span>
                  <span className="shrink-0 rounded-full bg-indigo-50 dark:bg-indigo-950/80 px-2 py-0.5 text-[11px] font-semibold text-indigo-700 dark:text-indigo-300 border border-indigo-200/60 dark:border-indigo-800/60">
                    Page {src.page}
                  </span>
                </div>
                <div className="text-slate-400 ml-2">
                  {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </div>
              </button>

              {isExpanded && (
                <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800/60 text-slate-600 dark:text-slate-300 italic text-[11.5px] leading-relaxed bg-slate-50/60 dark:bg-slate-950/40 p-2 rounded">
                  &ldquo;{src.excerpt}&rdquo;
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
