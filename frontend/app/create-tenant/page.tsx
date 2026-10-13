'use client';

import Link from 'next/link';
import { ArrowLeft, BarChart3 } from 'lucide-react';
import MultiStepSignupForm from '@/components/signup/MultiStepSignupForm';

export default function CreateTenantRoute() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-950 py-6 px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-8 max-w-2xl mx-auto w-full">
        <Link
          href="/"
          className="flex items-center gap-2 text-gray-300 hover:text-white transition font-semibold text-sm"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
        <Link
          href="/"
          className="flex items-center gap-2 text-gray-300 hover:text-white transition"
        >
          <div className="bg-white rounded p-1">
            <BarChart3 className="h-4 w-4 text-indigo-600" />
          </div>
          <span className="font-bold text-lg text-white">BlueOlive</span>
        </Link>
        <div className="w-12"></div>
      </div>

      <div className="flex-1 flex items-center justify-center">
        <div className="w-full max-w-2xl">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-white mb-2">Create Your Account</h1>
            <p className="text-gray-400">Set up your company&apos;s workspace</p>
          </div>

          <MultiStepSignupForm />
        </div>
      </div>
    </div>
  );
}
