"use client";

import { SearchBar } from "./SearchBar";
import { cn } from "@/lib/utils";

interface FloatingSearchBarProps {
  className?: string;
}

export function FloatingSearchBar({ className }: FloatingSearchBarProps) {
  return (
    <div
      className={cn(
        "fixed top-7 left-0 right-0 z-40 px-4 py-3",
        "transition-all duration-300",
        className,
      )}
    >
      <SearchBar variant="floating" />
    </div>
  );
}
