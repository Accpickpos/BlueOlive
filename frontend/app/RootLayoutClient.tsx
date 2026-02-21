'use client';

import { QueryProvider } from "@/lib/QueryProvider";
import { AuthProvider } from "@/lib/AuthContext";
import { ReactNode } from "react";
import { ChunkErrorHandler } from "./ChunkErrorHandler";
import Navbar from "@/components/navbar";

export function RootLayoutClient({ children }: { children: ReactNode }) {
  return (
    <QueryProvider>
      <AuthProvider>
        <ChunkErrorHandler>
          <div className="flex-1 flex flex-col">
            <Navbar />
            <main className="p-6">{children}</main>
          </div>
        </ChunkErrorHandler>
      </AuthProvider>
    </QueryProvider>
  );
}
