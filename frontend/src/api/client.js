// Centralized Axios client. Backend auth is a per-user signed session token minted at login —
// no API key, no cookies. Every request carries it as Authorization: Bearer <token>, once known.
import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('sessionToken');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }

  return config;
});

export default client;
