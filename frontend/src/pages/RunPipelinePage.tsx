import React, { useState, useEffect } from 'react';
import { RunConfigForm } from '../components/RunConfigForm';
import { ProfileSetSelector } from '../components/ProfileSetSelector';
import { DataSourceSelector, DataSourceType } from '../components/DataSourceSelector';
import { RunSummary } from '../components/RunSummary';
import { PlotGallery } from '../components/PlotGallery';
import { ProfileSummaryViewer } from '../components/ProfileSummaryViewer';
import { getDefaultConfig } from '../api/configApi';
import { runUpload, runUploadBatch, listPlots } from '../api/runsApi';
import { RunConfig, RunResult } from '../types';

export const RunPipelinePage: React.FC = () => {
  const [config, setConfig] = useState<RunConfig | null>(null);
  const [dataSource, setDataSource] = useState<{ type: DataSourceType; value: File[] } | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);
  const [plots, setPlots] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDefaultConfig().then(setConfig).catch(console.error);
  }, []);

  useEffect(() => {
    if (result) {
      listPlots(result.run_id)
        .then((data) => setPlots(data.plots))
        .catch(console.error);
    }
  }, [result]);

  const handleRun = async () => {
    if (!config || !dataSource) {
      setError('Please configure settings and select a data source');
      return;
    }

    setRunning(true);
    setError(null);
    setResult(null);

    try {
      console.log('Running pipeline with config:', {
        type: dataSource.type,
        filesCount: dataSource.value.length,
        config: config
      });

      let runResult: RunResult;
      if (dataSource.type === 'folder') {
        console.log('Calling runUploadBatch with', dataSource.value.length, 'files');
        runResult = await runUploadBatch(config, dataSource.value);
      } else {
        // dataSource.type === 'upload'
        console.log('Calling runUpload with file:', dataSource.value[0].name);
        runResult = await runUpload(config, dataSource.value[0]);
      }
      console.log('Pipeline run successful:', runResult);
      setResult(runResult);
    } catch (err: any) {
      console.error('Pipeline run failed:', err);
      console.error('Error response:', err.response);
      
      // Extract detailed error message
      let errorMessage = 'Failed to run pipeline';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      // Add status code if available
      if (err.response?.status) {
        errorMessage = `[${err.response.status}] ${errorMessage}`;
      }
      
      setError(errorMessage);
    } finally {
      setRunning(false);
    }
  };

  if (!config) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-sky-600 to-teal-500 flex items-center justify-center shadow-lg shadow-sky-900/50">
          <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-100">Run Pipeline</h1>
          <p className="text-gray-400">Configure and execute EEG analysis</p>
        </div>
      </div>

      <RunConfigForm config={config} onChange={setConfig} />

      <ProfileSetSelector
        value={config.profile_set_id}
        onChange={(id) => setConfig({ ...config, profile_set_id: id })}
      />

      <DataSourceSelector onSelect={(type, value) => setDataSource({ type, value })} />

      {dataSource && (
        <div className="px-4 py-3 bg-sky-900/30 border border-sky-700 rounded-xl">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm font-medium text-sky-400">
              Data source selected: {dataSource.type === 'folder' 
                ? `${dataSource.value.length} CSV files from folder` 
                : `File: ${dataSource.value[0].name}`}
            </span>
          </div>
        </div>
      )}

      {error && (
        <div className="px-4 py-3 bg-rose-900/30 border border-rose-700 text-rose-400 rounded-xl">
          <div className="flex items-start gap-2">
            <svg className="w-5 h-5 text-rose-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <strong className="font-semibold">Error:</strong> {error}
            </div>
          </div>
        </div>
      )}

      <button
        onClick={handleRun}
        disabled={running || !dataSource}
        className="w-full px-6 py-3.5 rounded-xl font-semibold bg-gradient-to-r from-sky-600 to-teal-500 hover:from-sky-500 hover:to-teal-400 text-white shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-sky-600 disabled:hover:to-teal-500 transform hover:-translate-y-0.5 active:translate-y-0"
      >
        {running ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Running Pipeline...
          </span>
        ) : (
          'Run Pipeline'
        )}
      </button>

      {result && (
        <>
          <RunSummary result={result} />
          {result.summary_xlsx && <ProfileSummaryViewer runId={result.run_id} />}
          <PlotGallery runId={result.run_id} plots={plots} />
        </>
      )}
    </div>
  );
};
