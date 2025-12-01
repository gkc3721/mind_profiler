import React from 'react';
import { BandThresholds } from '../types/config';

interface BandThresholdsEditorProps {
  bandThresholds: Record<string, BandThresholds>;
  onChange: (bandThresholds: Record<string, BandThresholds>) => void;
}

const BANDS = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma'] as const;
const THRESHOLD_KEYS: (keyof BandThresholds)[] = ['yuksek', 'yuksek_orta', 'orta', 'dusuk_orta'];
const THRESHOLD_LABELS: Record<keyof BandThresholds, string> = {
  yuksek: 'Yüksek',
  yuksek_orta: 'Yüksek-Orta',
  orta: 'Orta',
  dusuk_orta: 'Düşük-Orta'
};

// Default values if a band is missing
const DEFAULT_THRESHOLDS: Record<string, BandThresholds> = {
  Delta: { yuksek: 85, yuksek_orta: 75, orta: 50, dusuk_orta: 40 },
  Theta: { yuksek: 70, yuksek_orta: 60, orta: 40, dusuk_orta: 30 },
  Alpha: { yuksek: 80, yuksek_orta: 70, orta: 50, dusuk_orta: 40 },
  Beta: { yuksek: 52, yuksek_orta: 45, orta: 30, dusuk_orta: 22 },
  Gamma: { yuksek: 34, yuksek_orta: 27, orta: 18, dusuk_orta: 13 }
};

export const BandThresholdsEditor: React.FC<BandThresholdsEditorProps> = ({ bandThresholds, onChange }) => {
  const updateThreshold = (band: string, key: keyof BandThresholds, value: number) => {
    onChange({
      ...bandThresholds,
      [band]: {
        ...(bandThresholds[band] || DEFAULT_THRESHOLDS[band]),
        [key]: value
      }
    });
  };

  const getBandThresholds = (band: string): BandThresholds => {
    return bandThresholds[band] || DEFAULT_THRESHOLDS[band];
  };

  return (
    <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-xl">
      <div className="flex items-start gap-3 mb-6">
        <div className="text-teal-400 mt-1">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-gray-100">Band Thresholds</h2>
          <p className="text-sm text-gray-400 mt-1">
            Configure threshold values for each brain wave band classification
          </p>
        </div>
      </div>
      
      <div className="overflow-hidden rounded-xl border border-slate-700">
        <table className="w-full">
          <thead>
            <tr className="bg-gradient-to-r from-sky-600 to-teal-500">
              <th className="px-4 py-3 text-left font-semibold text-white">Band</th>
              {THRESHOLD_KEYS.map(key => (
                <th key={key} className="px-4 py-3 text-center font-semibold text-white">
                  {THRESHOLD_LABELS[key]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {BANDS.map((band, idx) => {
              const thresholds = getBandThresholds(band);
              return (
                <tr key={band} className={idx % 2 === 0 ? 'bg-slate-900' : 'bg-slate-800/50'}>
                  <td className="px-4 py-3 font-medium text-gray-200">{band}</td>
                  {THRESHOLD_KEYS.map(key => (
                    <td key={key} className="px-2 py-2">
                      <input
                        type="number"
                        value={thresholds[key]}
                        onChange={(e) => updateThreshold(band, key, parseFloat(e.target.value) || 0)}
                        className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-center text-gray-100 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all"
                        step="0.1"
                      />
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
