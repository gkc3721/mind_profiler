import React, { useState, useEffect } from 'react';
import { getDefaultConfig } from '../api/configApi';
import { RunConfig } from '../types/config';
import { RunConfigForm } from '../components/RunConfigForm';

export const ConfigPage: React.FC = () => {
  const [config, setConfig] = useState<RunConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await getDefaultConfig();
      setConfig(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="rounded-2xl bg-rose-900/30 border border-rose-700 p-6">
        <p className="text-rose-400">Error loading configuration</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-600 to-sky-500 flex items-center justify-center shadow-lg shadow-teal-900/50">
          <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-100">Default Configuration</h1>
          <p className="text-gray-400">View and adjust default pipeline parameters</p>
        </div>
      </div>

      {error && (
        <div className="px-4 py-3 bg-rose-900/30 border border-rose-700 text-rose-400 rounded-xl">
          <div className="flex items-start gap-2">
            <svg className="w-5 h-5 text-rose-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>{error}</div>
          </div>
        </div>
      )}

      {saved && (
        <div className="px-4 py-3 bg-teal-900/30 border border-teal-700 text-teal-400 rounded-xl">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-medium">Configuration saved!</span> (Note: These are defaults; actual runs use per-run configs)
          </div>
        </div>
      )}

      <div className="rounded-2xl bg-sky-900/20 border border-sky-700 p-4">
        <div className="flex items-start gap-2">
          <svg className="w-5 h-5 text-sky-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-gray-400">
            These are the default configuration values. When running the pipeline, you can override these values on a per-run basis.
          </p>
        </div>
      </div>

      <RunConfigForm config={config} onChange={setConfig} />

      <button
        onClick={() => setSaved(true)}
        className="px-6 py-3 rounded-xl font-semibold bg-gradient-to-r from-sky-600 to-teal-500 hover:from-sky-500 hover:to-teal-400 text-white shadow-lg transition-all duration-200"
      >
        Save Defaults (Future: persist to backend)
      </button>
    </div>
  );
};
