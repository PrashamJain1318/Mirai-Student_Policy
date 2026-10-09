'use client';

import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-20">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center space-x-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 font-bold text-white shadow-lg shadow-sky-500/20">
            M
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">
              MirAI <span className="text-sky-400">Student Policy Advisor</span>
            </h1>
            <p className="text-xs text-slate-400">
              Autonomous Handbook RAG • Mirai School of Technology 2026
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400 ring-1 ring-inset ring-emerald-500/20">
            ● Active LCEL Pipeline
          </span>
        </div>
      </div>
    </header>
  );
};
