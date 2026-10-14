import type { NextConfig } from 'next';
const config: NextConfig = {
  output: 'standalone',
  devIndicators: false,
  serverExternalPackages: ['pg'],
  turbopack: {root: process.cwd()},
  outputFileTracingExcludes: {'/*':['./.data/**/*','./.env*','./worker/.venv/**/*','./data/models/**/*','./docs/screenshots/**/*']},
  async headers() { return [{ source: '/(.*)', headers: [
    {key:'X-Content-Type-Options',value:'nosniff'},
    {key:'Referrer-Policy',value:'same-origin'},
    {key:'Permissions-Policy',value:'camera=(self), microphone=(self), geolocation=()'},
    {key:'Content-Security-Policy',value:"default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; worker-src 'self' blob:; frame-src 'self' blob:; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'"}
  ]}] }
};
export default config;
