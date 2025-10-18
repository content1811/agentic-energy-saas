import { Suspense } from "react";
import { Dashboard } from "@/components/dashboard";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Energy Dashboard
          </h1>
          <p className="mt-2 text-gray-600">
            Real-time monitoring and AI-powered recommendations
          </p>
        </header>
        
        <Suspense fallback={<div>Loading...</div>}>
          <Dashboard />
        </Suspense>
      </div>
    </main>
  );
}