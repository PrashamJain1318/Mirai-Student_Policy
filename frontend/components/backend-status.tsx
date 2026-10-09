'use client';

import React, { useEffect, useState, useCallback } from "react";
import { HealthStatus } from "../lib/types";
import { checkBackendHealth } from "../lib/api";
import { Activity, CheckCircle2, AlertTriangle, XCircle, RefreshCw } from "lucide-react";

interface BackendStatusProps {
  onStatusChange?: (status: HealthStatus) => void;
}

export const BackendStatus: React.FC<BackendStatusProps> = ({ onStatusChange }) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const pollHealth = useCallback(async () => {
    setIsRefreshing(true);
    const res = await checkBackendHealth();
    setHealth(res);
    if (onStatusChange) onStatusChange(res);
    setIsRefreshing(false);
  }, [onStatusChange]);

  useEffect(() => {
    let isMounted = true;
    checkBackendHealth().then((res) => {
      if (isMounted) {
        setHealth(res);
        if (onStatusChange) onStatusChange(res);
      }
    });

    const interval = setInterval(() => {
      checkBackendHealth().then((res) => {
        if (isMounted) {
          setHealth(res);
          if (onStatusChange) onStatusChange(res);
        }
      });
    }, 15000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [onStatusChange]);

  if (!health) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-3 text-xs text-slate-500 animate-pulse">
        Checking advisor service connectivity...
      </div>
    );
  }

  const isOffline = health.status === "offline";

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-3 shadow-xs">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800/80">
        <div className="flex items-center gap-1.5 font-semibold text-xs text-slate-700 dark:text-slate-300">
          <Activity className="w-3.5 h-3.5 text-indigo-500" />
          <span>System Readiness</span>
        </div>
        <button
          onClick={pollHealth}
          disabled={isRefreshing}
          className="text-slate-400 hover:text-indigo-600 transition-colors"
          title="Refresh connection status"
        >
          <RefreshCw className={`w-3 h-3 ${isRefreshing ? "animate-spin text-indigo-600" : ""}`} />
        </button>
      </div>

      <div className="mt-2 space-y-1.5 text-[11.5px]">
        {/* Backend API status */}
        <div className="flex items-center justify-between">
          <span className="text-slate-500 dark:text-slate-400">FastAPI Backend:</span>
          {isOffline ? (
            <span className="inline-flex items-center gap-1 text-rose-600 font-medium">
              <XCircle className="w-3 h-3" /> Offline
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-emerald-600 font-medium">
              <CheckCircle2 className="w-3 h-3" /> Online
            </span>
          )}
        </div>

        {/* Handbook Indexed status */}
        <div className="flex items-center justify-between">
          <span className="text-slate-500 dark:text-slate-400">Handbook Index:</span>
          {health.vector_store_initialized ? (
            <span className="inline-flex items-center gap-1 text-emerald-600 font-medium">
              <CheckCircle2 className="w-3 h-3" /> Ready ({health.indexed_chunks_count} chunks)
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-amber-600 font-medium">
              <AlertTriangle className="w-3 h-3" /> Not Indexed
            </span>
          )}
        </div>

        {/* API key configured */}
        <div className="flex items-center justify-between">
          <span className="text-slate-500 dark:text-slate-400">Gemini Key:</span>
          {health.api_key_configured ? (
            <span className="text-emerald-600 font-medium">Configured</span>
          ) : (
            <span className="text-amber-600 font-medium">Missing (.env)</span>
          )}
        </div>
      </div>
    </div>
  );
};
