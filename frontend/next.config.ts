import type { NextConfig } from "next";
import path from "path";

const internalApiBaseUrl =
  process.env.INTERNAL_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:18080/api";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: path.join(__dirname, ".."),
  allowedDevOrigins: ["127.0.0.1", "localhost", "*.local", "10.*", "172.*", "192.168.*"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${internalApiBaseUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
