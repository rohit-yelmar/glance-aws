"use client";

import Link from "next/link";
import { ShoppingBag, ShoppingCartIcon, Sparkles } from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { SearchBar } from "./SearchBar";

export function Header() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-white/90 backdrop-blur-sm shadow-lg"
          : "bg-white/80 backdrop-blur-md",
      )}
    >
      <div className="max-w-7xl pt-5 top-5 mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20 gap-4">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center gap-2 group flex-shrink-0"
          >
            <div className="relative">
              <Sparkles className="w-6 h-6 text-black" />
              <div className="absolute inset-0 blur-sm opacity-50 group-hover:opacity-100 transition-opacity">
                <Sparkles className="w-6 h-6 text-black" />
              </div>
            </div>
            <span className="text-2xl font-bold tracking-tight text-black">
              GLANCE
            </span>
          </Link>

          {/* Search Bar - Centered */}
          <div className="flex-1 max-w-2xl mx-auto">
            <SearchBar variant="inline" />
          </div>

          {/* Cart Button */}
          <button className="relative p-2 rounded-full hover:bg-black/5 transition-colors flex-shrink-0">
            <ShoppingCartIcon className="w-8 h-8 text-black" />
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-black text-white text-xs rounded-full flex items-center justify-center font-medium">
              0
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
