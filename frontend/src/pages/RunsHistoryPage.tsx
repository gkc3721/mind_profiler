import React, { useState, useEffect } from 'react';
import { RunSummary, RunResult } from '../types/runs';
import { listRuns, getRunDetails, listPlots, getLogUrl } from '../api/runsApi';
import { PlotGallery } from '../components/PlotGallery';

export const RunsHistoryPage: React.FC = () => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRun, setSelectedRun] = useState<RunResult | null>(null);
  const [plots, setPlots] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRuns();
  }, []);

  const loadRuns = async () => {
    try {
      const data = await listRuns();
      setRuns(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRunClick = async (runId: string) => {
    try {
      const details = await getRunDetails(runId);
      setSelectedRun(details);
      const plotsData = await listPlots(runId);
      setPlots(plotsData.plots);
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Runs History</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date/Time</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Profile Set</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Files</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Matched</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unmatched</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Config</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {runs.map((run) => (
              <tr
                key={run.run_id}
                onClick={() => handleRunClick(run.run_id)}
                className="cursor-pointer hover:bg-gray-50"
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {new Date(run.timestamp).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">{run.profile_set_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">{run.processed_files}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">{run.matched_count}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">{run.unmatched_count}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  Δ={run.dominance_delta}, B={run.balance_threshold}, W={run.window_secs}s
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedRun && (
        <div className="mt-6 bg-white p-6 rounded-lg shadow-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">Run Details: {selectedRun.run_id}</h2>
            <button
              onClick={() => setSelectedRun(null)}
              className="px-4 py-2 bg-gray-500 text-white rounded-md"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <p className="text-sm text-gray-600">Processed Files</p>
              <p className="text-xl font-bold">{selectedRun.processed_files}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Matched</p>
              <p className="text-xl font-bold text-green-600">{selectedRun.matched_count}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Unmatched</p>
              <p className="text-xl font-bold text-red-600">{selectedRun.unmatched_count}</p>
            </div>
          </div>

          <div className="mb-4">
            <h3 className="font-bold mb-2">Configuration</h3>
            <div className="bg-gray-50 p-4 rounded">
              <p>Dominance Delta: {selectedRun.config.dominance_delta}</p>
              <p>Balance Threshold: {selectedRun.config.balance_threshold}</p>
              <p>Window Seconds: {selectedRun.config.window_secs}</p>
              <p>Profile Set: {selectedRun.config.profile_set_id}</p>
            </div>
          </div>

          <div className="mb-4">
            <a
              href={getLogUrl(selectedRun.run_id)}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-blue-500 text-white rounded-md inline-block"
            >
              View Log
            </a>
            {selectedRun.summary_xlsx && (
              <a
                href={`http://localhost:8000${selectedRun.summary_xlsx.replace(/^.*\/runs/, '/runs')}`}
                download
                className="ml-2 px-4 py-2 bg-green-500 text-white rounded-md inline-block"
              >
                Download Summary Excel
              </a>
            )}
          </div>

          <PlotGallery runId={selectedRun.run_id} plots={plots} maxPreview={12} />
        </div>
      )}
    </div>
  );
};
