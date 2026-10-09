'use client';

import React, { useState, useRef } from "react";
import { ingestPolicyHandbook } from "../lib/api";
import { IngestResponse } from "../lib/types";
import { Upload, FileUp, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

interface DocumentUploaderProps {
  onIngestSuccess?: (res: IngestResponse) => void;
}

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({ onIngestSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError("Only PDF files are supported.");
        return;
      }
      setSelectedFile(file);
      setError(null);
      setResult(null);
    }
  };

  const handleIngest = async () => {
    setIsUploading(true);
    setError(null);
    try {
      const res = await ingestPolicyHandbook(selectedFile || undefined);
      setResult(res);
      if (onIngestSuccess) onIngestSuccess(res);
    } catch (err: unknown) {
      const errMsg =
        err instanceof Error
          ? err.message
          : "Ingestion failed. Please check backend connection and API key.";
      setError(errMsg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-3 shadow-xs">
      <div className="flex items-center gap-1.5 font-semibold text-xs text-slate-700 dark:text-slate-300 pb-2 border-b border-slate-100 dark:border-slate-800/80">
        <FileUp className="w-3.5 h-3.5 text-indigo-500" />
        <span>Policy Handbook Ingestion</span>
      </div>

      <div className="mt-2.5 space-y-2">
        <input
          type="file"
          accept=".pdf,application/pdf"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          id="handbook-upload-input"
        />

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="w-full flex items-center justify-center gap-2 rounded-lg border border-dashed border-slate-300 dark:border-slate-700 px-3 py-2 text-xs font-medium text-slate-600 dark:text-slate-300 hover:border-indigo-500 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
        >
          <Upload className="w-3.5 h-3.5 text-slate-400" />
          <span className="truncate">
            {selectedFile ? selectedFile.name : "Select custom handbook (optional)"}
          </span>
        </button>

        <button
          type="button"
          onClick={handleIngest}
          disabled={isUploading}
          className="w-full flex items-center justify-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white shadow-xs hover:bg-indigo-500 disabled:opacity-50 transition-colors"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Chunking & Indexing...</span>
            </>
          ) : (
            <span>
              {selectedFile ? "Upload & Ingest PDF" : "Index Official Handbook (2026)"}
            </span>
          )}
        </button>

        {error && (
          <div className="flex items-start gap-1.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 p-2 text-[11px] text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900/50">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span className="break-words">{error}</span>
          </div>
        )}

        {result && (
          <div className="rounded-lg bg-emerald-50 dark:bg-emerald-950/40 p-2 text-[11px] text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/50 space-y-1">
            <div className="flex items-center gap-1 font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>Ingestion Complete</span>
            </div>
            <div className="text-[10.5px] text-emerald-700 dark:text-emerald-400">
              • Chunks Created: <strong>{result.total_chunks}</strong> (Avg: {result.average_chunk_size} chars)
              <br />
              • Total In Index: <strong>{result.total_collection_count}</strong>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
