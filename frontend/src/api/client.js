// Centralized Axios client — attaches httpOnly JWT cookies automatically and retries requests after a 401 by hitting the refresh endpoint
import axios from 'axios';

const client = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  withCredentials: true,
});

client.interceptors.response.use(
  res => res,
  async err => {
    if (err.response?.status === 401) {
      await axios.post('/api/auth/refresh', {}, { withCredentials: true });
      return client(err.config);
    }
    return Promise.reject(err);
  }
);

export default client;
