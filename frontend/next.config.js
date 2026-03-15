/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://nginx/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
