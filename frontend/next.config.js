/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'assets.myntassets.com',
        pathname: '/assets/images/**',
      },
    ],
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/search',
        destination: 'http://localhost:8000/search',
      },
    ];
  },
};

module.exports = nextConfig;
