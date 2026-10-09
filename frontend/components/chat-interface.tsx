'use client';

import React, { useRef, useEffect } from "react";
import { ChatMessage } from "./chat-message";
import { ChatInput } from "./chat-input";
import { ChatMessage as ChatMessageType } from "../lib/types";
import { Sparkles, Bot, GraduationCap, ShieldCheck } from "lucide-react";

interface ChatInterfaceProps {
  messages: ChatMessageType[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  onRetry: () => void;
}

const SUGGESTED_QUESTIONS = [
  "I have 72% attendance. How many attendance marks will I get?",
  "I study at the Ratnam campus. How do I apply for medical leave?",
  "How do we propose a new student society?",
  "What does the handbook say about smoking on campus?",
];

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  isLoading,
  onSendMessage,
  onRetry,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-full bg-slate-50/40 dark:bg-slate-950/20">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
        <div className="mx-auto max-w-3xl">
          {messages.length === 0 ? (
            /* Empty State */
            <div className="my-10 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 mb-4 shadow-sm border border-indigo-100 dark:border-indigo-900/60">
                <GraduationCap className="w-7 h-7" />
              </div>
              <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 tracking-tight">
                Welcome to MirAI Policy Advisor
              </h2>
              <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
                Ask any question regarding Mirai School of Technology academic policies, attendance grading, medical leave, societies, or campus regulations.
              </p>

              {/* Suggested Questions Grid */}
              <div className="mt-8 text-left">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 dark:text-slate-400 mb-3">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
                  <span>Frequently Consulted Policies:</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {SUGGESTED_QUESTIONS.map((q, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => onSendMessage(q)}
                      className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 text-left text-xs font-medium text-slate-700 dark:text-slate-200 hover:border-indigo-500 hover:shadow-xs transition-all flex items-start justify-between gap-2 group"
                    >
                      <span>{q}</span>
                      <span className="text-indigo-500 dark:text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity">
                        →
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Zero Hallucination Guarantee */}
              <div className="mt-8 inline-flex items-center gap-2 rounded-full border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50 dark:bg-emerald-950/30 px-3.5 py-1.5 text-[11px] text-emerald-800 dark:text-emerald-300">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>Zero Hallucination Guardrails: Unverified claims are explicitly rejected.</span>
              </div>
            </div>
          ) : (
            /* Message Stream */
            <div className="space-y-2">
              {messages.map((m) => (
                <ChatMessage key={m.id} message={m} onRetry={onRetry} />
              ))}

              {isLoading && (
                <div className="flex items-start gap-3 mb-6">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-white shrink-0 shadow-sm mt-0.5 animate-pulse">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="rounded-2xl rounded-tl-xs border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-3 shadow-xs">
                    <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                      <div className="flex gap-1">
                        <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-bounce"></span>
                      </div>
                      <span>Retrieving handbook evidence &amp; verifying citations...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input Footer */}
      <div className="border-t border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/60 backdrop-blur-md p-4">
        <div className="mx-auto max-w-3xl">
          <ChatInput onSendMessage={onSendMessage} isLoading={isLoading} />
          <p className="mt-2 text-center text-[10.5px] text-slate-400">
            MirAI Advisor answers are strictly derived from the official Mirai School of Technology Handbook 2026.
          </p>
        </div>
      </div>
    </div>
  );
};
