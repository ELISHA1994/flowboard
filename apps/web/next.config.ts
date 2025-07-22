import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Disable trailing slash redirects to prevent conflicts with FastAPI
  skipTrailingSlashRedirect: true,
  // Ensure proper header forwarding
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Credentials',
            value: 'true',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
