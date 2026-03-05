"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { 
  ArrowLeft, 
  Star, 
  ShoppingBag, 
  Heart, 
  Share2,
  Check,
  Truck,
  RotateCcw,
  Shield
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import productsData from "@/lib/products.json";
import { Product } from "@/lib/types";
import { formatPrice, parseProductAttributes } from "@/lib/utils";

// Available sizes
const sizes = ["XS", "S", "M", "L", "XL", "XXL"];

export default function ProductDetailPage() {
  const params = useParams();
  const id = parseInt(params.id as string);
  
  const [product, setProduct] = useState<Product | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState(0);
  const [isWishlisted, setIsWishlisted] = useState(false);

  useEffect(() => {
    // Find product from local data
    const found = productsData.find((p) => p.p_id === id);
    if (found) {
      setProduct(found);
    }
    setIsLoading(false);
  }, [id]);

  if (isLoading) {
    return <ProductDetailSkeleton />;
  }

  if (!product) {
    return (
      <div className="text-center py-20">
        <h1 className="text-2xl font-bold text-black mb-4">Product Not Found</h1>
        <p className="text-gray-500 mb-6">The product you're looking for doesn't exist.</p>
        <Link href="/">
          <Button className="rounded-full bg-black">Back to Home</Button>
        </Link>
      </div>
    );
  }

  const avgRating = typeof product.avg_rating === "string" 
    ? parseFloat(product.avg_rating) || 0 
    : product.avg_rating || 0;
  
  const ratingCount = typeof product.ratingCount === "string"
    ? parseInt(product.ratingCount) || 0
    : product.ratingCount || 0;

  const attributes = parseProductAttributes(product.p_attributes);
  
  // Parse description to extract key details
  const descriptionItems = product.description
    .split(/<\/?[^>]+>/)
    .filter(item => item.trim() && !item.includes("br") && !item.includes("b"))
    .slice(0, 6);

  return (
    <div className="space-y-8">
      {/* Back Button */}
      <Link href="/">
        <Button variant="outline" className="rounded-full border-black">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Products
        </Button>
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
        {/* Left: Image Gallery */}
        <div className="flex gap-4">
          {/* Thumbnail Sidebar */}
          <div className="hidden sm:flex flex-col gap-3 w-20">
            {[0, 1, 2, 3].map((index) => (
              <button
                key={index}
                onClick={() => setSelectedImage(index)}
                className={`relative aspect-square rounded-xl overflow-hidden border-2 transition-all ${
                  selectedImage === index 
                    ? "border-black" 
                    : "border-transparent hover:border-gray-300"
                }`}
              >
                <Image
                  src={product.img}
                  alt={`${product.name} - view ${index + 1}`}
                  fill
                  className="object-cover"
                  sizes="80px"
                />
              </button>
            ))}
          </div>

          {/* Main Image */}
          <div className="flex-1 relative aspect-[3/4] rounded-2xl overflow-hidden bg-gray-100 group">
            <Image
              src={product.img}
              alt={product.name}
              fill
              className="object-cover transition-transform duration-500 group-hover:scale-105"
              sizes="(max-width: 1024px) 100vw, 50vw"
              priority
            />
            
            {/* Mobile Thumbnail Dots */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 sm:hidden">
              {[0, 1, 2, 3].map((index) => (
                <button
                  key={index}
                  onClick={() => setSelectedImage(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    selectedImage === index ? "bg-black w-4" : "bg-white/70"
                  }`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Right: Product Info */}
        <div className="space-y-6">
          {/* Header */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="rounded-full">
                {product.brand}
              </Badge>
              <Badge variant="outline" className="rounded-full">
                {product.colour}
              </Badge>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-black leading-tight">
              {product.name}
            </h1>
            
            {/* Rating */}
            {avgRating > 0 && (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  <span className="font-medium text-black">{avgRating.toFixed(1)}</span>
                </div>
                <span className="text-gray-400">|</span>
                <span className="text-gray-500 text-sm">
                  {ratingCount.toLocaleString()} reviews
                </span>
              </div>
            )}
          </div>

          {/* Price */}
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-black">
              {formatPrice(product.price)}
            </span>
            <span className="text-gray-500 line-through">
              {formatPrice(Math.round(product.price * 1.2))}
            </span>
            <Badge className="bg-green-100 text-green-800 hover:bg-green-100 rounded-full">
              20% OFF
            </Badge>
          </div>

          <Separator />

          {/* Size Selector */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-medium text-black">Select Size</span>
              <button className="text-sm text-gray-500 underline hover:text-black">
                Size Guide
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {sizes.map((size) => (
                <button
                  key={size}
                  onClick={() => setSelectedSize(size)}
                  className={`w-12 h-12 rounded-full border-2 font-medium transition-all ${
                    selectedSize === size
                      ? "border-black bg-black text-white"
                      : "border-gray-200 hover:border-black hover:bg-gray-50"
                  }`}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button 
              className="flex-1 h-14 rounded-full bg-black hover:bg-black/90 text-base font-medium"
              disabled={!selectedSize}
            >
              <ShoppingBag className="w-5 h-5 mr-2" />
              Add to Bag
            </Button>
            <Button
              variant="outline"
              size="icon"
              className={`h-14 w-14 rounded-full border-2 ${
                isWishlisted 
                  ? "border-red-500 text-red-500" 
                  : "border-black"
              }`}
              onClick={() => setIsWishlisted(!isWishlisted)}
            >
              <Heart className={`w-5 h-5 ${isWishlisted ? "fill-current" : ""}`} />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-14 w-14 rounded-full border-2 border-black"
            >
              <Share2 className="w-5 h-5" />
            </Button>
          </div>

          {!selectedSize && (
            <p className="text-sm text-gray-500 text-center">
              Please select a size to add to bag
            </p>
          )}

          <Separator />

          {/* Benefits */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center space-y-2">
              <Truck className="w-6 h-6 mx-auto text-gray-600" />
              <p className="text-xs text-gray-600">Free Shipping</p>
            </div>
            <div className="text-center space-y-2">
              <RotateCcw className="w-6 h-6 mx-auto text-gray-600" />
              <p className="text-xs text-gray-600">Easy Returns</p>
            </div>
            <div className="text-center space-y-2">
              <Shield className="w-6 h-6 mx-auto text-gray-600" />
              <p className="text-xs text-gray-600">Secure Payment</p>
            </div>
          </div>

          <Separator />

          {/* Description */}
          <div className="space-y-3">
            <h3 className="font-medium text-black">Product Details</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              {descriptionItems.map((item, index) => (
                <li key={index} className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Attributes */}
          {Object.keys(attributes).length > 0 && (
            <div className="space-y-3">
              <h3 className="font-medium text-black">Specifications</h3>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(attributes)
                  .slice(0, 6)
                  .map(([key, value]) => (
                    <div key={key} className="text-sm">
                      <span className="text-gray-500">{key}:</span>
                      <span className="ml-1 text-black font-medium">{value}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ProductDetailSkeleton() {
  return (
    <div className="space-y-8">
      <Skeleton className="h-10 w-32 rounded-full" />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
        {/* Image Skeleton */}
        <div className="flex gap-4">
          <div className="hidden sm:flex flex-col gap-3 w-20">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="aspect-square rounded-xl" />
            ))}
          </div>
          <Skeleton className="flex-1 aspect-[3/4] rounded-2xl" />
        </div>

        {/* Info Skeleton */}
        <div className="space-y-6">
          <div className="flex gap-2">
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-6 w-20 rounded-full" />
          </div>
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-12 w-48" />
          <Skeleton className="h-px w-full" />
          <div className="space-y-3">
            <Skeleton className="h-4 w-24" />
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <Skeleton key={i} className="w-12 h-12 rounded-full" />
              ))}
            </div>
          </div>
          <div className="flex gap-3">
            <Skeleton className="h-14 flex-1 rounded-full" />
            <Skeleton className="h-14 w-14 rounded-full" />
            <Skeleton className="h-14 w-14 rounded-full" />
          </div>
        </div>
      </div>
    </div>
  );
}
