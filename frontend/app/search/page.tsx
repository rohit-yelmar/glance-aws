"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Sparkles, ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { ProductCard, ProductCardSkeleton } from "@/components/ProductCard";
import { SearchResponse, SearchResult } from "@/lib/types";
import { Button } from "@/components/ui/button";

function SearchResultsContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!query) {
      setIsLoading(false);
      return;
    }

    async function performSearch() {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await fetch("http://localhost:8000/search", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query,
            limit: 10,
          }),
        });

        if (!response.ok) {
          throw new Error("Search failed");
        }

        const data: SearchResponse = await response.json();
        setResults(data.results);
      } catch (err) {
        setError("Unable to connect to search service. Please make sure the backend is running.");
        console.error("Search error:", err);
      } finally {
        setIsLoading(false);
      }
    }

    performSearch();
  }, [query]);

  if (!query) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-500">Enter a search query to find products</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-8">
        {/* Loading Header */}
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="outline" size="icon" className="rounded-full">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <div>
            <div className="h-6 bg-gray-200 rounded w-48 animate-pulse" />
            <div className="h-4 bg-gray-200 rounded w-32 mt-2 animate-pulse" />
          </div>
        </div>

        {/* Loading Animation */}
        <div className="flex flex-col items-center justify-center py-16 space-y-4">
          <div className="relative">
            <Loader2 className="w-12 h-12 animate-spin text-black" />
            <div className="absolute inset-0 blur-lg">
              <Loader2 className="w-12 h-12 animate-spin text-black/30" />
            </div>
          </div>
          <div className="text-center space-y-2">
            <p className="text-lg font-medium text-black">AI is searching...</p>
            <p className="text-sm text-gray-500">Analyzing your query and finding the best matches</p>
          </div>
        </div>

        {/* Skeleton Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <ProductCardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20 space-y-4">
        <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
          <Sparkles className="w-8 h-8 text-gray-400" />
        </div>
        <h2 className="text-xl font-semibold text-black">Search Error</h2>
        <p className="text-gray-500 max-w-md mx-auto">{error}</p>
        <Link href="/">
          <Button className="rounded-full mt-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="outline" size="icon" className="rounded-full border-black">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-black">
              Search Results
            </h1>
            <p className="text-gray-500 text-sm">
              {results.length} results for "<span className="font-medium text-black">{query}</span>"
            </p>
          </div>
        </div>
        
        {results.length > 0 && (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Sparkles className="w-4 h-4 text-black" />
            <span>Powered by Glance AI</span>
          </div>
        )}
      </div>

      {/* Results Grid */}
      {results.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 stagger-children">
          {results.map((result) => (
            <ProductCard 
              key={result.product_id} 
              product={result} 
              confidenceScore={result.confidence_score}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-20 space-y-4">
          <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
            <Sparkles className="w-8 h-8 text-gray-400" />
          </div>
          <h2 className="text-xl font-semibold text-black">No results found</h2>
          <p className="text-gray-500 max-w-md mx-auto">
            We couldn't find any products matching "{query}". 
            Try using different keywords or browse our featured products.
          </p>
          <Link href="/">
            <Button className="rounded-full mt-4 bg-black hover:bg-black/90">
              Browse All Products
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="space-y-8">
        <div className="flex items-center gap-4">
          <div className="h-10 w-10 bg-gray-200 rounded-full animate-pulse" />
          <div>
            <div className="h-6 bg-gray-200 rounded w-48 animate-pulse" />
            <div className="h-4 bg-gray-200 rounded w-32 mt-2 animate-pulse" />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <ProductCardSkeleton key={i} />
          ))}
        </div>
      </div>
    }>
      <SearchResultsContent />
    </Suspense>
  );
}
