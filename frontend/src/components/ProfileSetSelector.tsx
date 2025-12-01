import React, { useEffect, useState } from 'react';
import { listProfileSets } from '../api/profilesApi';
import { ProfileSetSummary } from '../types/profiles';

interface ProfileSetSelectorProps {
  value: string;
  onChange: (profileSetId: string) => void;
}

export const ProfileSetSelector: React.FC<ProfileSetSelectorProps> = ({ value, onChange }) => {
  const [profileSets, setProfileSets] = useState<ProfileSetSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listProfileSets()
      .then(setProfileSets)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-xl">
        <div className="text-gray-400">Loading profile sets...</div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-xl">
      <div className="flex items-start gap-3 mb-6">
        <div className="text-teal-400 mt-1">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div className="flex-1">
          <h2 className="text-2xl font-semibold tracking-tight text-gray-100">Profile Set</h2>
          <p className="text-sm text-gray-400 mt-1">Select the mental profile set to use for analysis</p>
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium tracking-wide uppercase text-gray-400 mb-1.5">
          Active Profile Set
        </label>
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-gray-100 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all"
        >
          {profileSets.map((ps) => (
            <option key={ps.id} value={ps.id} className="bg-slate-800">
              {ps.name} ({ps.profile_count} profiles)
            </option>
          ))}
        </select>
        <p className="text-xs text-gray-500 mt-1">
          {profileSets.find(ps => ps.id === value)?.description || 'No description available'}
        </p>
      </div>
    </div>
  );
};
