import axios from 'axios';

// Use relative URLs in production (served from same origin)
// Use localhost:8000 in development
const baseURL = import.meta.env.DEV 
  ? 'http://localhost:8000' 
  : window.location.origin;

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
