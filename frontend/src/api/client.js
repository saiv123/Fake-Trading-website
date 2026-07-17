// Centralized Axios client. Backend auth has no cookies/JWT — every request carries a static
// X-API-Key (this website's pre-shared key) plus X-User-Id for the acting user, once known.
import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

client.interceptors.request.use((config) => {
  config.headers['X-API-Key'] = import.meta.env.VITE_WEBSITE_API_KEY;

  const userId = localStorage.getItem('userId');
  if (userId) {
    config.headers['X-User-Id'] = userId;
  }

  return config;
});

export default client;
