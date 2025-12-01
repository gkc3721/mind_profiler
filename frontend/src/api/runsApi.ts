import { apiClient } from './client';
import { RunConfig } from '../types/config';
import { RunResult, RunSummary } from '../types/runs';

// Get base URL (same logic as client.ts)
const getBaseUrl = () => {
  return import.meta.env.DEV ? 'http://localhost:8000' : window.location.origin;
};

export const runBatch = async (config: RunConfig): Promise<RunResult> => {
  const response = await apiClient.post<RunResult>('/run/batch', config);
  return response.data;
};

export const runSingle = async (config: RunConfig, csvPath: string): Promise<RunResult> => {
  const response = await apiClient.post<RunResult>('/run/single', {
    ...config,
    csv_path: csvPath,
  });
  return response.data;
};

export const runUpload = async (config: RunConfig, file: File): Promise<RunResult> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('config', JSON.stringify(config));
  
  const response = await apiClient.post<RunResult>('/run/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const runUploadBatch = async (config: RunConfig, files: File[]): Promise<RunResult> => {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });
  formData.append('config', JSON.stringify(config));
  
  const response = await apiClient.post<RunResult>('/run/upload-batch', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const listRuns = async (): Promise<RunSummary[]> => {
  const response = await apiClient.get<RunSummary[]>('/runs');
  return response.data;
};

export const getRunDetails = async (runId: string): Promise<RunResult> => {
  const response = await apiClient.get<RunResult>(`/runs/${runId}`);
  return response.data;
};

export const listPlots = async (runId: string): Promise<{ plots: string[] }> => {
  const response = await apiClient.get<{ plots: string[] }>(`/runs/${runId}/plots`);
  return response.data;
};

export const getPlotUrl = (runId: string, filename: string): string => {
  return `${getBaseUrl()}/runs/${runId}/plots/${filename}`;
};

export const getLogUrl = (runId: string): string => {
  return `${getBaseUrl()}/runs/${runId}/log`;
};

export const getSummaryData = async (runId: string): Promise<any> => {
  const response = await apiClient.get(`/runs/${runId}/summary`);
  return response.data;
};

export const getSummaryDownloadUrl = (runId: string): string => {
  return `${getBaseUrl()}/runs/${runId}/summary/download`;
};
