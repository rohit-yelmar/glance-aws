"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Search, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SearchBarProps {
  variant?: "floating" | "inline";
  initialQuery?: string;
}

export function SearchBar({
  variant = "inline",
  initialQuery = "",
}: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSearch = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!query.trim()) return;

      setIsLoading(true);

      // Navigate to search results page
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);

      // Reset loading after navigation
      setTimeout(() => setIsLoading(false), 500);
    },
    [query, router],
  );

  const isFloating = variant === "floating";

  return (
    <form
      onSubmit={handleSearch}
      className={cn(
        "relative flex items-center transition-all duration-300",
        isFloating ? "w-full max-w-2xl mx-auto" : "w-full max-w-2xl",
      )}
    >
      <div
        className={cn(
          "relative w-full flex items-center bg-white/90 backdrop-blur-xl border shadow-lg",
          isFloating ? "rounded-full h-14 shadow-xl" : "rounded-2xl h-14",
          "transition-all duration-300 focus-within:shadow-xl focus-within:border-black/10",
          isLoading && "opacity-90",
        )}
      >
        {/* AI Sparkle Icon */}
        <div className="absolute left-5 flex items-center justify-center">
          <div className="relative">
            <Sparkles className="w-5 h-5 text-black sparkle" />
            <div className="absolute inset-0 blur-sm">
              <Sparkles className="w-5 h-5 text-black/30" />
            </div>
          </div>
        </div>

        {/* Search Input */}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search with AI..."
          disabled={isLoading}
          className={cn(
            "w-full bg-transparent outline-none text-gray-800 placeholder:text-gray-400",
            "h-full pl-14 pr-36",
            isFloating ? "rounded-full" : "rounded-2xl",
            "text-base font-normal",
          )}
        />

        {/* Powered by Glance Badge */}
        <div className="absolute -right-5 -translate-x-1/2 pointer-events-none hidden sm:block">
          <div className="flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-orange-300 to-orange-200 rounded-full border border-gray-200/50">
            <Sparkles className="w-3 h-3 text-black" />
            <span className="text-xs font-medium text-black whitespace-nowrap">
              Powered by Glance
            </span>
          </div>
        </div>

        {/* Search Button */}
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className={cn(
            "absolute right-2 flex items-center justify-center",
            "w-10 h-10 rounded-full bg-black text-white",
            "transition-all duration-200 hover:bg-gray-800 hover:scale-105",
            "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100",
          )}
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Search className="w-4 h-4" />
          )}
        </button>
      </div>
    </form>
  );
}

// Loading state component for search results
export function SearchLoadingState() {
  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      <div className="flex items-center justify-center gap-3 py-8">
        <Loader2 className="w-6 h-6 animate-spin text-black" />
        <span className="text-gray-600 font-medium">AI is searching...</span>
      </div>
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-2xl animate-pulse" />
        ))}
      </div>
    </div>
  );
}
