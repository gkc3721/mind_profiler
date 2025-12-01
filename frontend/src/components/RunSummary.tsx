import React from 'react';
import { RunResult } from '../types/runs';

interface RunSummaryProps {
  result: RunResult;
}

export const RunSummary: React.FC<RunSummaryProps> = ({ result }) => {
  return (
    <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-xl">
      <div className="flex items-start gap-3 mb-6">
        <div className="text-teal-400 mt-1">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <div className="flex-1">
          <h2 className="text-2xl font-semibold tracking-tight text-gray-100">Run Results</h2>
          <p className="text-sm text-gray-400 mt-1">Summary of the pipeline execution</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-gradient-to-br from-sky-900/40 to-sky-800/30 rounded-xl border border-sky-700/50">
          <p className="text-xs font-medium tracking-wide uppercase text-gray-400 mb-1">Processed Files</p>
          <p className="text-3xl font-bold text-sky-400">{result.processed_files}</p>
        </div>
        <div className="p-4 bg-gradient-to-br from-teal-900/40 to-teal-800/30 rounded-xl border border-teal-700/50">
          <p className="text-xs font-medium tracking-wide uppercase text-gray-400 mb-1">Matched</p>
          <p className="text-3xl font-bold text-teal-400">{result.matched_count}</p>
        </div>
        <div className="p-4 bg-gradient-to-br from-amber-900/40 to-amber-800/30 rounded-xl border border-amber-700/50">
          <p className="text-xs font-medium tracking-wide uppercase text-gray-400 mb-1">Unmatched</p>
          <p className="text-3xl font-bold text-amber-400">{result.unmatched_count}</p>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 space-y-1">
        <p className="text-sm text-gray-400">
          <span className="font-medium text-gray-300">Run ID:</span> <span className="font-mono text-gray-500">{result.run_id}</span>
        </p>
        <p className="text-sm text-gray-400">
          <span className="font-medium text-gray-300">Timestamp:</span> {new Date(result.timestamp).toLocaleString()}
        </p>
      </div>
    </div>
  );
};
