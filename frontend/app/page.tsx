'use client';

import React, { useState } from "react";
import { Sidebar } from "../components/sidebar";
import { ChatInterface } from "../components/chat-interface";
import { useChat } from "../hooks/use-chat";
import { Menu, X, GraduationCap } from "lucide-react";

export default function Home() {
  const { messages, isLoading, sendMessage, clearMessages, retryLastMessage } = useChat();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100">
      {/* Desktop Sidebar */}
      <div className="hidden md:flex h-full">
        <Sidebar
          onClearChat={clearMessages}
          messageCount={messages.length}
        />
      </div>

      {/* Mobile Drawer Backdrop */}
      {mobileSidebarOpen && (
        <div
          onClick={() => setMobileSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-xs md:hidden"
        />
      )}

      {/* Mobile Drawer */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-72 transform bg-white dark:bg-slate-950 transition-transform duration-300 ease-in-out md:hidden ${
          mobileSidebarOpen ? "translate-x-0" : "-translate-x-100"
        }`}
      >
        <div className="relative h-full flex flex-col">
          <button
            onClick={() => setMobileSidebarOpen(false)}
            className="absolute top-4 right-4 z-10 text-slate-400 hover:text-slate-700"
          >
            <X className="w-5 h-5" />
          </button>
          <Sidebar
            onClearChat={() => {
              clearMessages();
              setMobileSidebarOpen(false);
            }}
            messageCount={messages.length}
          />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col h-full overflow-hidden">
        {/* Top Header */}
        <header className="flex h-14 items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-950/70 backdrop-blur-md px-4 shrink-0">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileSidebarOpen(true)}
              className="text-slate-500 hover:text-slate-800 md:hidden"
              title="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white md:hidden">
                <GraduationCap className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Autonomous MirAI Student Policy Advisor
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-full bg-indigo-50 dark:bg-indigo-950/70 px-2.5 py-1 text-[11px] font-medium text-indigo-700 dark:text-indigo-300 border border-indigo-200/60 dark:border-indigo-800/60">
              LCEL + Gemini 3.8 Flash
            </span>
          </div>
        </header>

        {/* Chat Interface */}
        <main className="flex-1 overflow-hidden">
          <ChatInterface
            messages={messages}
            isLoading={isLoading}
            onSendMessage={sendMessage}
            onRetry={retryLastMessage}
          />
        </main>
      </div>
    </div>
  );
}
