import { ProductCard, ProductCardSkeleton } from "@/components/ProductCard";
import productsData from "@/lib/products.json";
import { Product } from "@/lib/types";
import { Suspense } from "react";

export default function HomePage() {
  // Get first 24 products for the home page
  const products: Product[] = productsData.slice(0, 24);

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="text-center py-10 space-y-4">
        <h1 className="text-4xl md:text-5xl font-bold text-black tracking-tight">
          Discover Fashion with AI
        </h1>
        <p className="text-gray-600 text-lg max-w-2xl mx-auto">
          Search naturally. Find exactly what you're looking for with Glance's
          intelligent product search powered by advanced AI.
        </p>
      </section>

      {/* Products Grid */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-black">
            Featured Products
          </h2>
          <span className="text-sm text-gray-500">
            Showing {products.length} products
          </span>
        </div>

        <Suspense fallback={<ProductsGridSkeleton />}>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 stagger-children">
            {products.map((product) => (
              <ProductCard key={product.p_id} product={product} />
            ))}
          </div>
        </Suspense>
      </section>
    </div>
  );
}

function ProductsGridSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {Array.from({ length: 8 }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  );
}
