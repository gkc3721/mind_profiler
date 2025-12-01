import React from 'react';
import { RunConfig } from '../types/config';
import { BandThresholdsEditor } from './BandThresholdsEditor';

interface RunConfigFormProps {
  config: RunConfig;
  onChange: (config: RunConfig) => void;
}

export const RunConfigForm: React.FC<RunConfigFormProps> = ({ config, onChange }) => {
  const updateField = <K extends keyof RunConfig>(field: K, value: RunConfig[K]) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-xl">
        <div className="flex items-start gap-3 mb-6">
          <div className="text-sky-400 mt-1">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
          </div>
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-gray-100">Core Thresholds</h2>
            <p className="text-sm text-gray-400 mt-1">Configure the main pipeline parameters</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-medium tracking-wide uppercase text-gray-400 mb-1.5">
              Dominance Delta
            </label>
            <input
              type="number"
              step="0.1"
              value={config.dominance_delta}
              onChange={(e) => updateField('dominance_delta', parseFloat(e.target.value))}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-gray-100 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all"
            />
            <p className="text-xs text-gray-500 mt-1">Used for dominance detection between bands</p>
          </div>

          <div>
            <label className="block text-xs font-medium tracking-wide uppercase text-gray-400 mb-1.5">
              Balance Threshold
            </label>
            <input
              type="number"
              step="0.1"
              value={config.balance_threshold}
              onChange={(e) => updateField('balance_threshold', parseFloat(e.target.value))}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-gray-100 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all"
            />
            <p className="text-xs text-gray-500 mt-1">Threshold for balance classification</p>
          </div>

          <div>
            <label className="block text-xs font-medium tracking-wide uppercase text-gray-400 mb-1.5">
              Denge Mean Threshold
            </label>
            <input
              type="number"
              step="0.1"
              value={config.denge_mean_threshold}
              onChange={(e) => updateField('denge_mean_threshold', parseFloat(e.target.value))}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-gray-100 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all"
            />
            <p className="text-xs text-gray-500 mt-1">Mean balance threshold parameter</p>
          </div>

          <div>
            <label className="block text-xs font-medium tracking-wide uppercase text-gray-400 mb-1.5">
              Window Seconds
            </label>
            <input
              type="number"
              value={config.window_secs}
              onChange={(e) => updateField('window_secs', parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-gray-100 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all"
            />
            <p className="text-xs text-gray-500 mt-1">Analysis window size in seconds</p>
          </div>

          <div>
            <label className="block text-xs font-medium tracking-wide uppercase text-gray-400 mb-1.5">
              Window Samples
            </label>
            <input
              type="number"
              value={config.window_samples}
              onChange={(e) => updateField('window_samples', parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-gray-100 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all"
            />
            <p className="text-xs text-gray-500 mt-1">Number of samples per window</p>
          </div>
        </div>
      </div>

      <BandThresholdsEditor
        bandThresholds={config.band_thresholds}
        onChange={(bandThresholds) => updateField('band_thresholds', bandThresholds)}
      />
    </div>
  );
};
