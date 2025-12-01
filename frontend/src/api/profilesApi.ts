import { apiClient } from './client';
import { ProfileSet, ProfileSetSummary } from '../types/profiles';

export const listProfileSets = async (): Promise<ProfileSetSummary[]> => {
  const response = await apiClient.get<ProfileSetSummary[]>('/profiles');
  return response.data;
};

export const getProfileSet = async (id: string): Promise<ProfileSet> => {
  const response = await apiClient.get<ProfileSet>(`/profiles/${id}`);
  return response.data;
};

export const saveProfileSet = async (profileSet: ProfileSet): Promise<ProfileSet> => {
  const response = await apiClient.put<ProfileSet>(`/profiles/${profileSet.id}`, profileSet);
  return response.data;
};

export const createProfileSet = async (profileSet: ProfileSet): Promise<ProfileSet> => {
  const response = await apiClient.post<ProfileSet>('/profiles', profileSet);
  return response.data;
};

export const deleteProfileSet = async (id: string): Promise<void> => {
  await apiClient.delete(`/profiles/${id}`);
};
