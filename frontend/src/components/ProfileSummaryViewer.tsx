import React, { useState, useEffect } from 'react';
import { getSummaryData, getSummaryDownloadUrl } from '../api/runsApi';

interface ProfileSummaryViewerProps {
  runId: string;
}

export const ProfileSummaryViewer: React.FC<ProfileSummaryViewerProps> = ({ runId }) => {
  const [summaryData, setSummaryData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSheet, setActiveSheet] = useState<string>('');

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true);
        const data = await getSummaryData(runId);
        setSummaryData(data);
        // Set first sheet as active by default
        if (data.sheets && Object.keys(data.sheets).length > 0) {
          setActiveSheet(Object.keys(data.sheets)[0]);
        }
      } catch (err: any) {
        console.error('Error loading summary:', err);
        setError(err.response?.data?.detail || 'Failed to load summary');
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [runId]);

  if (loading) {
    return (
      <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-xl">
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-400">Loading profile summary...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl bg-rose-900/30 border border-rose-700 p-6">
        <div className="flex items-start gap-2">
          <svg className="w-5 h-5 text-rose-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="font-medium text-rose-400">Could not load summary</p>
            <p className="text-sm text-rose-300 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!summaryData || !summaryData.sheets) {
    return null;
  }

  const sheetNames = Object.keys(summaryData.sheets);
  const currentSheetData = summaryData.sheets[activeSheet] || [];

  // Get column names from first row
  const columns = currentSheetData.length > 0 ? Object.keys(currentSheetData[0]) : [];

  return (
    <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-start gap-3">
          <div className="text-emerald-400 mt-1">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-semibold tracking-tight text-gray-100">Profile Summary</h2>
            <p className="text-sm text-gray-400 mt-1">View analysis results by sheet</p>
          </div>
        </div>
        <a
          href={getSummaryDownloadUrl(runId)}
          download
          className="px-4 py-2 rounded-xl font-medium bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-md transition-all duration-200 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Download Excel
        </a>
      </div>

      {/* Sheet tabs */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
        {sheetNames.map((sheetName) => (
          <button
            key={sheetName}
            onClick={() => setActiveSheet(sheetName)}
            className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-all duration-200 ${
              activeSheet === sheetName
                ? 'bg-gradient-to-r from-sky-600 to-teal-500 text-white shadow-md'
                : 'bg-slate-800 text-gray-400 hover:text-gray-200 hover:bg-slate-700'
            }`}
          >
            {sheetName}
          </button>
        ))}
      </div>

      {/* Table */}
      {currentSheetData.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>No data in this sheet</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-700">
          <table className="w-full">
            <thead>
              <tr className="bg-gradient-to-r from-sky-600 to-teal-500">
                {columns.map((col) => (
                  <th key={col} className="px-4 py-3 text-left font-semibold text-white text-sm">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {currentSheetData.map((row: any, idx: number) => (
                <tr key={idx} className={idx % 2 === 0 ? 'bg-slate-900' : 'bg-slate-800/50'}>
                  {columns.map((col) => (
                    <td key={col} className="px-4 py-3 text-sm text-gray-300">
                      {row[col] !== null && row[col] !== undefined ? String(row[col]) : '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Row count */}
      <div className="mt-4 text-sm text-gray-500 text-right">
        {currentSheetData.length} row{currentSheetData.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
};
