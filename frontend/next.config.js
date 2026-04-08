/** @type {import('next').NextConfig} */
const nextConfig = {
  skipTrailingSlashRedirect: true,

  async rewrites() {
    const apiProxyTarget = process.env.INTERNAL_API_PROXY_TARGET ?? "http://nginx/api";

    return [
      {
        source: "/api/:path*",
        destination: `${apiProxyTarget}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
