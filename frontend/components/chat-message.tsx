'use client';

import React from "react";
import { ChatMessage as ChatMessageType } from "../lib/types";
import { SourceCitationsList } from "./source-citation";
import { Bot, User, AlertCircle, Info, RefreshCw } from "lucide-react";

interface ChatMessageProps {
  message: ChatMessageType;
  onRetry?: () => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onRetry }) => {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="flex items-start gap-2 max-w-[80%]">
          <div className="rounded-2xl rounded-tr-xs bg-indigo-600 px-4 py-2.5 text-sm text-white shadow-xs">
            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
            <span className="mt-1 block text-right text-[10px] text-indigo-200">
              {message.timestamp}
            </span>
          </div>
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 shrink-0 text-xs font-semibold">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-6">
      <div className="flex items-start gap-3 max-w-[90%] md:max-w-[85%]">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-white shrink-0 shadow-sm mt-0.5">
          <Bot className="w-4 h-4" />
        </div>

        <div className="rounded-2xl rounded-tl-xs border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-3 text-sm text-slate-800 dark:text-slate-200 shadow-xs flex-1">
          {/* Abstention alert banner */}
          {message.abstained && (
            <div className="mb-3 flex items-center gap-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 px-2.5 py-1.5 text-xs text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-900/60 font-medium">
              <Info className="w-3.5 h-3.5 shrink-0" />
              <span>Evidence Abstention: Question cannot be established from the handbook excerpts.</span>
            </div>
          )}

          {/* Error banner */}
          {message.isError && (
            <div className="mb-3 flex items-center justify-between rounded-lg bg-rose-50 dark:bg-rose-950/40 px-2.5 py-1.5 text-xs text-rose-800 dark:text-rose-300 border border-rose-200 dark:border-rose-900/60">
              <div className="flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>Backend communication failure</span>
              </div>
              {onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className="flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium text-rose-700 hover:bg-rose-100 dark:hover:bg-rose-900/40"
                >
                  <RefreshCw className="w-3 h-3" /> Retry
                </button>
              )}
            </div>
          )}

          {/* Main answer text */}
          <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap leading-relaxed">
            {message.content}
          </div>

          {/* MultiQuery subqueries badge if expanded */}
          {message.sub_queries && message.sub_queries.length > 1 && (
            <div className="mt-2 text-[11px] text-slate-400">
              <span className="font-medium text-slate-500">MultiQuery Expanded Perspectives:</span>{" "}
              {message.sub_queries.slice(1).join(" • ")}
            </div>
          )}

          {/* Verified Source Citations */}
          {message.sources && message.sources.length > 0 && (
            <SourceCitationsList sources={message.sources} />
          )}

          <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400">
            <span>MirAI Grounded RAG • 0.0 Temp</span>
            <span>{message.timestamp}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
