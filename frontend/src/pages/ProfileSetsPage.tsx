import React, { useState, useEffect } from 'react';
import { ProfileSet, ProfileDefinition, WAVE_LEVELS } from '../types/profiles';
import { listProfileSets, getProfileSet, saveProfileSet, createProfileSet, deleteProfileSet } from '../api/profilesApi';
import { ProfileSetSummary } from '../types/profiles';

export const ProfileSetsPage: React.FC = () => {
  const [profileSets, setProfileSets] = useState<ProfileSetSummary[]>([]);
  const [currentProfileSet, setCurrentProfileSet] = useState<ProfileSet | null>(null);
  const [selectedId, setSelectedId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newProfileSetName, setNewProfileSetName] = useState('');

  useEffect(() => {
    loadProfileSets();
  }, []);

  useEffect(() => {
    if (selectedId) {
      loadProfileSet(selectedId);
    }
  }, [selectedId]);

  const loadProfileSets = async () => {
    try {
      const sets = await listProfileSets();
      setProfileSets(sets);
      if (sets.length > 0 && !selectedId) {
        setSelectedId(sets[0].id);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const loadProfileSet = async (id: string) => {
    setLoading(true);
    try {
      const ps = await getProfileSet(id);
      setCurrentProfileSet(ps);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!currentProfileSet) return;
    try {
      await saveProfileSet(currentProfileSet);
      setError(null);
      alert('Profile set saved successfully!');
      loadProfileSets();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleCreateNew = async () => {
    if (!newProfileSetName.trim()) return;
    const newId = newProfileSetName.toLowerCase().replace(/\s+/g, '_');
    const newProfileSet: ProfileSet = {
      id: newId,
      name: newProfileSetName,
      description: '',
      profiles: [],
    };
    try {
      await createProfileSet(newProfileSet);
      setNewProfileSetName('');
      await loadProfileSets();
      setSelectedId(newId);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDuplicate = async () => {
    if (!currentProfileSet) return;
    const newName = `${currentProfileSet.name} (Copy)`;
    const newId = `${currentProfileSet.id}_copy`;
    const duplicated: ProfileSet = {
      ...currentProfileSet,
      id: newId,
      name: newName,
    };
    try {
      await createProfileSet(duplicated);
      await loadProfileSets();
      setSelectedId(newId);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDelete = async () => {
    if (!selectedId || selectedId === 'meditasyon') {
      alert('Cannot delete default profile set');
      return;
    }
    if (!confirm(`Delete profile set "${selectedId}"?`)) return;
    try {
      await deleteProfileSet(selectedId);
      await loadProfileSets();
      if (profileSets.length > 1) {
        const remaining = profileSets.filter((ps) => ps.id !== selectedId);
        setSelectedId(remaining[0]?.id || '');
      } else {
        setSelectedId('');
        setCurrentProfileSet(null);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const updateProfile = (index: number, field: keyof ProfileDefinition, value: string) => {
    if (!currentProfileSet) return;
    const updated = [...currentProfileSet.profiles];
    updated[index] = { ...updated[index], [field]: value };
    setCurrentProfileSet({ ...currentProfileSet, profiles: updated });
  };

  const addProfile = () => {
    if (!currentProfileSet) return;
    const newProfile: ProfileDefinition = {
      id: `PROFILE_${currentProfileSet.profiles.length + 1}`,
      display_name: '',
      delta_level: 'orta',
      theta_level: 'orta',
      alpha_level: 'orta',
      beta_level: 'orta',
      gamma_level: 'orta',
    };
    setCurrentProfileSet({
      ...currentProfileSet,
      profiles: [...currentProfileSet.profiles, newProfile],
    });
  };

  const removeProfile = (index: number) => {
    if (!currentProfileSet) return;
    const updated = currentProfileSet.profiles.filter((_, i) => i !== index);
    setCurrentProfileSet({ ...currentProfileSet, profiles: updated });
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Profile Sets</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <div className="flex gap-4 items-end mb-4">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">Select Profile Set</label>
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
            >
              {profileSets.map((ps) => (
                <option key={ps.id} value={ps.id}>
                  {ps.name}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleSave}
            disabled={!currentProfileSet}
            className="px-4 py-2 bg-green-500 text-white rounded-md disabled:bg-gray-300"
          >
            Save
          </button>
          <button
            onClick={handleDuplicate}
            disabled={!currentProfileSet}
            className="px-4 py-2 bg-blue-500 text-white rounded-md disabled:bg-gray-300"
          >
            Duplicate
          </button>
          <button
            onClick={handleDelete}
            disabled={!selectedId || selectedId === 'meditasyon'}
            className="px-4 py-2 bg-red-500 text-white rounded-md disabled:bg-gray-300"
          >
            Delete
          </button>
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={newProfileSetName}
            onChange={(e) => setNewProfileSetName(e.target.value)}
            placeholder="New profile set name"
            className="flex-1 px-3 py-2 border rounded-md"
          />
          <button
            onClick={handleCreateNew}
            className="px-4 py-2 bg-purple-500 text-white rounded-md"
          >
            Create New
          </button>
        </div>
      </div>

      {loading && <div>Loading...</div>}

      {currentProfileSet && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-bold mb-4">{currentProfileSet.name}</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 px-4 py-2">Profile Name</th>
                  <th className="border border-gray-300 px-4 py-2">Delta</th>
                  <th className="border border-gray-300 px-4 py-2">Theta</th>
                  <th className="border border-gray-300 px-4 py-2">Alpha</th>
                  <th className="border border-gray-300 px-4 py-2">Beta</th>
                  <th className="border border-gray-300 px-4 py-2">Gamma</th>
                  <th className="border border-gray-300 px-4 py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {currentProfileSet.profiles.map((profile, index) => (
                  <tr key={index}>
                    <td className="border border-gray-300 px-4 py-2">
                      <input
                        type="text"
                        value={profile.display_name}
                        onChange={(e) => updateProfile(index, 'display_name', e.target.value)}
                        className="w-full px-2 py-1 border rounded"
                      />
                    </td>
                    {(['delta_level', 'theta_level', 'alpha_level', 'beta_level', 'gamma_level'] as const).map((field) => (
                      <td key={field} className="border border-gray-300 px-4 py-2">
                        <select
                          value={profile[field]}
                          onChange={(e) => updateProfile(index, field, e.target.value)}
                          className="w-full px-2 py-1 border rounded"
                        >
                          {WAVE_LEVELS.map((level) => (
                            <option key={level} value={level}>
                              {level}
                            </option>
                          ))}
                        </select>
                      </td>
                    ))}
                    <td className="border border-gray-300 px-4 py-2">
                      <button
                        onClick={() => removeProfile(index)}
                        className="px-2 py-1 bg-red-500 text-white rounded text-sm"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button
            onClick={addProfile}
            className="mt-4 px-4 py-2 bg-green-500 text-white rounded-md"
          >
            Add Profile
          </button>
        </div>
      )}
    </div>
  );
};
