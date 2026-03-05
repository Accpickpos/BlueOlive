import type { NextConfig } from "next";

// Bundle analyzer configuration (only runs when ANALYZE=true)
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig: NextConfig = {
  // Enable Turbopack configuration
  // Required when using webpack config with Turbopack (Next.js 16 default)
  turbopack: {},

  // Enable experimental optimizations for better performance
  experimental: {
    // Optimize package imports to reduce bundle size
    optimizePackageImports: [
      'lucide-react',
      '@radix-ui/react-select',
      '@radix-ui/react-tabs',
      '@radix-ui/react-slot',
      'recharts',
    ],
    // Reduce memory usage in development
    optimizeCss: true,
    // Limit the number of parallel builds
    workerThreads: false,
    cpus: 1,
  },
  
  // Enable compression
  compress: true,
  
  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    // Add domains if you have external images
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  
  // Reduce page cache for memory efficiency in dev
  onDemandEntries: {
    maxInactiveAge: 30 * 1000, // 30 seconds
    pagesBufferLength: 2,
  },
  
  // Disable x-powered-by header
  poweredByHeader: false,
  
  // Generate ETags for better caching
  generateEtags: true,
};

// Wrap with bundle analyzer
export default withBundleAnalyzer(nextConfig);
