import axios from 'axios';

// API Base URL - will be the tunneled backend
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types matching the FastAPI backend
export interface HealthCheck {
  status: string; 
  timestamp: string;
  version: string;
}

export interface RunCreate {
  name: string;
  description?: string;
  account: string;
  adapter_type?: string;
}

export interface RunInfo {
  run_id: string;
  name: string;
  description?: string;
  status: string;
  created_at: string;
  updated_at?: string;
  stages?: Record<string, StageInfo>;
  parameters?: Record<string, any>;
  account?: string;
}

export interface StageInfo {
  status: string;
  updated_at?: string;
  job_id?: string;
}

export interface StageSubmit {
  account: string;
  confirm_rerun?: boolean;
}

export interface JobStatus {
  run_id: string;
  stage: string;
  status: string;
  job_id?: string;
  updated_at?: string;
}

export interface StageLogs {
  stage: string;
  job_id: string;
  stdout: string | null;
  stderr: string | null;
  stdout_file: string | null;
  stderr_file: string | null;
}

export interface SuccessResponse {
  message: string;
  data?: any;
}

export interface SampleValidation {
  valid: boolean;
  samples?: Array<{ sample_id: string; files: string[] }>;
  errors?: string[];
}

export interface StageValidation {
  valid: boolean;
  errors: string[];
  warnings: string[];
  stage: string;
  run_id: string;
}

export interface QCResults {
  qc_raw?: {
    completed: boolean;
    multiqc_available: boolean;
    fastqc_available: boolean;
    files: Array<{
      name: string;
      path: string;
      type: string;
      description: string;
    }>;
  };
  qc_trimmed?: {
    completed: boolean;
    multiqc_available: boolean;
    fastqc_available: boolean;
    files: Array<{
      name: string;
      path: string;
      type: string;
      description: string;
    }>;
  };
}

export interface StorageInfo {
  data_directory: string;
  install_directory: string;
  runs_directory: string;
  storage_type: string;
  storage_description: string;
  user: string;
  persistent: boolean;
  info: string;
}

export interface UserInfo {
  username: string;
  uid: number;
  computing_id: string;
}

// API functions
export const api = {
  // Health check
  health: async (): Promise<HealthCheck> => {
    const response = await apiClient.get('/health');
    return response.data as HealthCheck;
  },

  // Get user information
  getUserInfo: async (): Promise<UserInfo> => {
    const response = await apiClient.get('/user');
    return response.data as UserInfo;
  },

  // Get storage information
  getStorageInfo: async (): Promise<StorageInfo> => {
    const response = await apiClient.get('/storage-info');
    return response.data as StorageInfo;
  },

  // Get SLURM accounts (no caching - use refresh button instead)
  getAccounts: async (): Promise<string[]> => {
    const response = await apiClient.get('/accounts');
    return response.data as string[];
  },

  // Refresh accounts (same as getAccounts now that caching is removed)
  refreshAccounts: async (): Promise<string[]> => {
    return api.getAccounts();
  },

  // Get pipeline stages
  getStages: async (): Promise<{ stages: string[] }> => {
    const response = await apiClient.get('/stages');
    return response.data as { stages: string[] };
  },

  // Run management
  createRun: async (runData: RunCreate): Promise<RunInfo> => {
    const response = await apiClient.post('/runs', runData);
    return response.data as RunInfo;
  },

  getRuns: async (): Promise<RunInfo[]> => {
    const response = await apiClient.get('/runs');
    return response.data as RunInfo[];
  },

  getRun: async (runId: string): Promise<RunInfo> => {
    const response = await apiClient.get(`/runs/${runId}`);
    return response.data as RunInfo;
  },

  deleteRun: async (runId: string): Promise<SuccessResponse> => {
    const response = await apiClient.delete(`/runs/${runId}`);
    return response.data as SuccessResponse;
  },

  // File upload
  uploadFiles: async (runId: string, formData: FormData): Promise<SuccessResponse> => {
    const response = await apiClient.post(`/runs/${runId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data as SuccessResponse;
  },

  // Sample validation
  validateSamples: async (runId: string): Promise<SampleValidation> => {
    const response = await apiClient.get(`/runs/${runId}/samples`);
    return response.data as SampleValidation;
  },

  // Stage management
  validateStage: async (runId: string, stage: string): Promise<StageValidation> => {
    const response = await apiClient.get(`/runs/${runId}/stages/${stage}/validate`);
    return response.data as StageValidation;
  },

  submitStage: async (runId: string, stage: string, stageData: StageSubmit): Promise<SuccessResponse> => {
    const response = await apiClient.post(`/runs/${runId}/stages/${stage}`, stageData);
    return response.data as SuccessResponse;
  },

  getStageStatus: async (runId: string, stage: string): Promise<JobStatus> => {
    const response = await apiClient.get(`/runs/${runId}/stages/${stage}/status`);
    return response.data as JobStatus;
  },

  getStageLogs: async (runId: string, stage: string): Promise<StageLogs> => {
    const response = await apiClient.get(`/runs/${runId}/stages/${stage}/logs`);
    return response.data as StageLogs;
  },

  // Results
  getResults: async (runId: string, resultType: string): Promise<any> => {
    const response = await apiClient.get(`/runs/${runId}/results/${resultType}`);
    return response.data;
  },

  // QC Results
  getQCResults: async (runId: string): Promise<QCResults> => {
    const response = await apiClient.get(`/runs/${runId}/qc/list`);
    return response.data as QCResults;
  },

  getQCFileUrl: (runId: string, stage: string, filePath: string): string => {
    return `${API_BASE_URL}/runs/${runId}/qc/${stage}/${filePath}`;
  },

  updateAdapterType: async (runId: string, adapterType: string): Promise<SuccessResponse> => {
    const response = await apiClient.put(`/runs/${runId}/adapter`, {
      adapter_type: adapterType
    });
    return response.data as SuccessResponse;
  },

  // featureCounts Results
  getFeatureCountsSummary: async (runId: string): Promise<any> => {
    const response = await apiClient.get(`/runs/${runId}/featurecounts-summary`);
    return response.data;
  },

  // DESeq2 Results
  getDESeq2Results: async (runId: string): Promise<any> => {
    const response = await apiClient.get(`/runs/${runId}/deseq2-results`);
    return response.data;
  },

  downloadDESeq2File: (runId: string, fileType: string): string => {
    return `${API_BASE_URL}/runs/${runId}/deseq2-download/${fileType}`;
  },
};

export default apiClient;