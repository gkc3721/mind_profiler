import React, { useState } from 'react';
import { getPlotUrl } from '../api/runsApi';

interface PlotGalleryProps {
  runId: string;
  plots: string[];
  maxPreview?: number;
}

export const PlotGallery: React.FC<PlotGalleryProps> = ({ runId, plots, maxPreview = 9 }) => {
  const [selectedPlot, setSelectedPlot] = useState<string | null>(null);
  const previewPlots = plots.slice(0, maxPreview);

  if (plots.length === 0) {
    return (
      <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-xl">
        <div className="text-center py-8 text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          No plots available
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-xl">
      <div className="flex items-start gap-3 mb-6">
        <div className="text-sky-400 mt-1">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-2xl font-semibold tracking-tight text-gray-100">Plots</h3>
          <p className="text-sm text-gray-400 mt-1">{plots.length} plot{plots.length !== 1 ? 's' : ''} generated</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {previewPlots.map((plot) => (
          <div
            key={plot}
            className="group cursor-pointer rounded-xl overflow-hidden border border-slate-700 hover:border-sky-500 hover:shadow-lg hover:shadow-sky-900/30 transition-all duration-200"
            onClick={() => setSelectedPlot(plot)}
          >
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-2">
              <img
                src={getPlotUrl(runId, plot)}
                alt={plot}
                className="w-full h-40 object-contain"
              />
            </div>
            <div className="p-3 bg-slate-900 border-t border-slate-800">
              <p className="text-xs text-gray-400 truncate group-hover:text-sky-400 transition">{plot}</p>
            </div>
          </div>
        ))}
      </div>

      {plots.length > maxPreview && (
        <div className="mt-4 text-center">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 text-gray-400 rounded-full text-sm">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Showing {maxPreview} of {plots.length} plots
          </span>
        </div>
      )}

      {selectedPlot && (
        <div
          className="fixed inset-0 bg-slate-950/90 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedPlot(null)}
        >
          <div className="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
            <div className="sticky top-0 bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
              <h4 className="font-semibold text-gray-100">{selectedPlot}</h4>
              <button
                onClick={() => setSelectedPlot(null)}
                className="p-2 hover:bg-slate-800 rounded-lg transition text-gray-400 hover:text-gray-200"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 bg-slate-800">
              <img
                src={getPlotUrl(runId, selectedPlot)}
                alt={selectedPlot}
                className="w-full h-auto"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
