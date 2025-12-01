import { apiClient } from './client';
import { RunConfig } from '../types/config';

export const getDefaultConfig = async (): Promise<RunConfig> => {
  const response = await apiClient.get<RunConfig>('/config/default');
  return response.data;
};
