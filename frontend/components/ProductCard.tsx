"use client";

import Link from "next/link";
import Image from "next/image";
import { Star } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Product, SearchResult } from "@/lib/types";
import { formatPrice, truncateText } from "@/lib/utils";

interface ProductCardProps {
  product: Product | SearchResult;
  confidenceScore?: number;
}

function isProduct(item: Product | SearchResult): item is Product {
  return "p_id" in item;
}

export function ProductCard({ product, confidenceScore }: ProductCardProps) {
  const id = isProduct(product) ? product.p_id : product.product_id;
  const name = product.name;
  const price = product.price;
  const imageUrl = isProduct(product) ? product.img : product.image_url;
  
  // Get rating for full Product type
  const avgRating = isProduct(product) 
    ? typeof product.avg_rating === "string" 
      ? parseFloat(product.avg_rating) || 0 
      : product.avg_rating || 0
    : 0;
  
  const ratingCount = isProduct(product)
    ? typeof product.ratingCount === "string"
      ? parseInt(product.ratingCount) || 0
      : product.ratingCount || 0
    : 0;

  // Get brand and colour for full Product type
  const brand = isProduct(product) ? product.brand : "";
  const colour = isProduct(product) ? product.colour : "";

  return (
    <Link href={`/product/${id}`}>
      <Card className="group overflow-hidden hover-lift cursor-pointer border-0">
        {/* Image Container */}
        <div className="relative aspect-[3/4] overflow-hidden bg-gray-100">
          <Image
            src={imageUrl}
            alt={name}
            fill
            className="object-cover transition-transform duration-500 group-hover:scale-105"
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
          />
          
          {/* Confidence Score Badge (for search results) */}
          {confidenceScore !== undefined && (
            <div className="absolute top-3 left-3 z-10">
              <Badge 
                variant="default" 
                className="bg-black/80 text-white text-xs backdrop-blur-sm"
              >
                {(confidenceScore * 100).toFixed(0)}% match
              </Badge>
            </div>
          )}

          {/* Brand Badge */}
          {brand && (
            <div className="absolute top-3 right-3 z-10">
              <Badge 
                variant="secondary" 
                className="bg-white/90 text-black text-xs backdrop-blur-sm"
              >
                {brand}
              </Badge>
            </div>
          )}

          {/* Hover Overlay */}
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-300" />
        </div>

        {/* Content */}
        <div className="p-4 space-y-2">
          {/* Product Name */}
          <h3 className="font-medium text-sm text-gray-900 line-clamp-2 min-h-[2.5rem]">
            {truncateText(name, 60)}
          </h3>

          {/* Colour */}
          {colour && (
            <p className="text-xs text-gray-500 capitalize">
              {colour}
            </p>
          )}

          {/* Price and Rating Row */}
          <div className="flex items-center justify-between pt-1">
            {/* Price */}
            <span className="font-semibold text-base text-black">
              {formatPrice(price)}
            </span>

            {/* Rating */}
            {avgRating > 0 && (
              <div className="flex items-center gap-1">
                <Star className="w-3.5 h-3.5 fill-yellow-400 text-yellow-400" />
                <span className="text-xs text-gray-600">
                  {avgRating.toFixed(1)}
                </span>
                {ratingCount > 0 && (
                  <span className="text-xs text-gray-400">
                    ({ratingCount.toLocaleString()})
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>
    </Link>
  );
}

// Skeleton loader for product cards
export function ProductCardSkeleton() {
  return (
    <div className="space-y-4">
      <div className="aspect-[3/4] bg-gray-200 rounded-2xl animate-pulse" />
      <div className="space-y-2">
        <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse" />
        <div className="h-3 bg-gray-200 rounded w-1/2 animate-pulse" />
        <div className="flex justify-between pt-1">
          <div className="h-4 bg-gray-200 rounded w-20 animate-pulse" />
          <div className="h-3 bg-gray-200 rounded w-16 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
