'use client';

import React from "react";
import { BackendStatus } from "./backend-status";
import { DocumentUploader } from "./document-uploader";
import { Trash2, ShieldCheck, GraduationCap } from "lucide-react";

interface SidebarProps {
  onClearChat: () => void;
  messageCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ onClearChat, messageCount }) => {
  return (
    <aside className="w-80 shrink-0 border-r border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/40 p-4 flex flex-col justify-between h-full overflow-y-auto">
      <div className="space-y-4">
        {/* Brand identity */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-md shadow-indigo-600/20 shrink-0">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="font-bold text-slate-900 dark:text-white text-base tracking-tight">
                MirAI Advisor
              </h1>
              <span className="rounded-full bg-indigo-100 dark:bg-indigo-950 px-2 py-0.5 text-[10px] font-semibold text-indigo-700 dark:text-indigo-300">
                2026
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
              Your University Policies. Clear Answers. Verified Sources.
            </p>
          </div>
        </div>

        {/* Backend health status card */}
        <BackendStatus />

        {/* Handbook Ingestion card */}
        <DocumentUploader />

        {/* Guardrail explanation */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-3 shadow-xs">
          <div className="flex items-center gap-1.5 font-semibold text-xs text-slate-700 dark:text-slate-300 mb-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>Factual Guardrails</span>
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
            Every answer is strictly synthesized from retrieved handbook excerpts using LCEL &amp; Gemini 3.8 Flash at temperature 0.0. When evidence is unavailable or contradictory, the advisor politely abstains rather than speculating.
          </p>
        </div>
      </div>

      {/* Bottom controls */}
      <div className="pt-4 border-t border-slate-200 dark:border-slate-800/80 mt-4 space-y-2">
        <button
          type="button"
          onClick={onClearChat}
          disabled={messageCount === 0}
          className="w-full flex items-center justify-center gap-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-rose-600 hover:border-rose-200 dark:hover:border-rose-900/50 disabled:opacity-40 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear Conversation</span>
        </button>
        <div className="text-center text-[10.5px] text-slate-400">
          Mirai School of Technology • Student Affairs
        </div>
      </div>
    </aside>
  );
};
