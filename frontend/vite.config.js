import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const { API_PROXY_TARGET, VITE_API_BASE_URL = '/api' } = loadEnv(mode, process.cwd(), '');
  const base = VITE_API_BASE_URL.replace(/\/+$/, '');
  const proxy = API_PROXY_TARGET && base.startsWith('/') && !base.startsWith('//')
    ? { [base]: { target: API_PROXY_TARGET, changeOrigin: true } }
    : undefined;
  return { server: { proxy }, preview: { proxy } };
});
