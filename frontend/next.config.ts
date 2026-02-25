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
  
  // Ensure proper chunk handling in development
  onDemandEntries: {
    // Keep pages in memory for longer during dev
    maxInactiveAge: 60 * 1000, // 1 minute
    pagesBufferLength: 5,
  },
  
  // Webpack configuration for bundle optimization
  webpack: (config, { isServer }) => {
    // Optimize moment.js imports if used - redirect to dayjs for smaller bundle
    config.resolve.alias = {
      ...config.resolve.alias,
      moment: 'dayjs',
    };
    
    // Only run on client-side builds
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    
    return config;
  },
  
  // Enable React strict mode for development (helps catch issues early)
  reactStrictMode: true,
  
  // Powered by header - disable for security
  poweredByHeader: false,
  
  // Generate ETags for better caching
  generateEtags: true,
};

// Wrap with bundle analyzer
export default withBundleAnalyzer(nextConfig);
