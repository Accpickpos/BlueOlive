import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/navbar";
import { AuthProvider } from "@/lib/AuthContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "BlueOlive - Retail Management System",
  description: "A modern, multi-tenant retail management and inventory system for small to medium-sized businesses",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="flex bg-gray-100">
        <AuthProvider>
          <div className="flex-1 flex flex-col">
            {/* <Navbar /> */}
            <main className="p-6">{children}</main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}