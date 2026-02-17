import type { NextConfig } from "next";

const nextConfig: NextConfig = {
 
  // Ensure proper chunk handling in development
  onDemandEntries: {
    // Keep pages in memory for longer during dev
    maxInactiveAge: 60 * 1000, // 1 minute
    pagesBufferLength: 5,
  },
  // Disable react strict mode temporarily if chunk errors persist
  // reactStrictMode: false,
};

export default nextConfig;
