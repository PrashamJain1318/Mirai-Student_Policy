'use client';

import React from 'react';
import { SourceCitation } from '../types';

interface CitationCardProps {
  citation: SourceCitation;
  index: number;
}

export const CitationCard: React.FC<CitationCardProps> = ({ citation, index }) => {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/80 p-3 text-sm text-slate-200 transition-all hover:border-sky-500">
      <div className="flex items-center justify-between pb-1 text-xs text-sky-400 font-medium">
        <span>
          [{index + 1}] {citation.policy_name}
        </span>
        <span className="rounded bg-sky-950 px-2 py-0.5 text-sky-300">
          Page {citation.page_number}
        </span>
      </div>
      <div className="font-semibold text-slate-100">{citation.section}</div>
      <p className="mt-1 line-clamp-3 text-xs text-slate-400 italic">
        &ldquo;{citation.snippet}&rdquo;
      </p>
    </div>
  );
};
