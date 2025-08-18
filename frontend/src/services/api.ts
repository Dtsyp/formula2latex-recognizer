import axios from 'axios';
import type { 
  User, 
  UserLogin, 
  UserRegister, 
  Token, 
  Wallet, 
  Transaction, 
  MLModel, 
  Task, 
  PredictionRequest, 
  TopUpRequest 
} from '../types';
import { API_BASE_URL } from '../utils/constants';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth-storage');
  if (token) {
    try {
      const authData = JSON.parse(token);
      if (authData.state?.token) {
        config.headers.Authorization = `Bearer ${authData.state.token}`;
      }
    } catch (error) {
      console.error('Error parsing auth token:', error);
    }
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear auth data
      localStorage.removeItem('auth-storage');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (credentials: UserLogin): Promise<{ user: User; token: string; wallet: Wallet }> => {
    const response = await api.post<Token>('/auth/login', {
      email: credentials.email,
      password: credentials.password,
    });
    
    // Get user profile with the token
    const userResponse = await api.get<User>('/auth/me', {
      headers: {
        Authorization: `Bearer ${response.data.access_token}`,
      },
    });
    
    // Get wallet info
    const walletResponse = await api.get<{id: string; balance: string}>('/wallet', {
      headers: {
        Authorization: `Bearer ${response.data.access_token}`,
      },
    });
    
    return {
      user: userResponse.data,
      token: response.data.access_token,
      wallet: {
        ...walletResponse.data,
        balance: parseFloat(walletResponse.data.balance)
      },
    };
  },

  register: async (userData: UserRegister): Promise<{ user: User; token: string; wallet: Wallet }> => {
    await api.post<User>('/auth/register', userData);
    
    // Auto-login after registration
    return authAPI.login({
      email: userData.email,
      password: userData.password,
    });
  },

  getProfile: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};

// Wallet API
export const walletAPI = {
  getWallet: async (): Promise<Wallet> => {
    const response = await api.get<{id: string; balance: string}>('/wallet');
    return {
      ...response.data,
      balance: parseFloat(response.data.balance)
    };
  },

  topUp: async (data: TopUpRequest): Promise<Transaction> => {
    const response = await api.post<Transaction>('/wallet/top-up', data);
    return response.data;
  },

  getTransactions: async (): Promise<Transaction[]> => {
    const response = await api.get<Transaction[]>('/wallet/transactions');
    return response.data;
  },
};

// Models API
export const modelsAPI = {
  getModels: async (): Promise<MLModel[]> => {
    const response = await api.get<MLModel[]>('/models');
    return response.data;
  },

  getModel: async (modelId: string): Promise<MLModel> => {
    const response = await api.get<MLModel>(`/models/${modelId}`);
    return response.data;
  },
};

// Tasks API
export const tasksAPI = {
  getTasks: async (): Promise<Task[]> => {
    const response = await api.get<Task[]>('/tasks');
    return response.data;
  },

  getTask: async (taskId: string): Promise<Task> => {
    const response = await api.get<Task>(`/tasks/${taskId}`);
    return response.data;
  },

  createPrediction: async (data: PredictionRequest): Promise<Task> => {
    const response = await api.post<Task>('/predict/', data);
    return response.data;
  },

  // Alternative method for file upload
  uploadFormula: async (file: File, modelId: string): Promise<Task> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_id', modelId);

    const response = await api.post<Task>('/predict/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Admin API
export const adminAPI = {
  getAllUsers: async (): Promise<User[]> => {
    const response = await api.get<User[]>('/admin/users');
    return response.data;
  },

  getAllTasks: async (): Promise<Task[]> => {
    const response = await api.get<Task[]>('/admin/tasks');
    return response.data;
  },

  getStats: async (): Promise<{
    total_users: number;
    total_tasks: number;
    total_credits_used: number;
    avg_success_rate: number;
  }> => {
    const response = await api.get('/admin/stats');
    return response.data;
  },
};

export default api;