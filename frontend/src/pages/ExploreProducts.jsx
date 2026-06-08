import { useEffect, useState, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, SlidersHorizontal, X, PackageSearch } from 'lucide-react'
import { getProducts, getCategories } from '../services/api'
import { useAuth } from '../context/AuthContext'
import ProductCard from '../components/ProductCard'
import { GridSkeleton } from '../components/LoadingSpinner'

const PRICE_RANGES = [
  { label: 'Any Price', min: null, max: null },
  { label: 'Under $25', min: null, max: 25 },
  { label: '$25 – $100', min: 25, max: 100 },
  { label: '$100 – $300', min: 100, max: 300 },
  { label: 'Over $300', min: 300, max: null },
]

export default function ExploreProducts() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchInput, setSearchInput] = useState(searchParams.get('search') || '')
  const { updateCartCount } = useAuth()

  // Active filters from URL params
  const activeCategory = searchParams.get('category') || ''
  const activeSearch = searchParams.get('search') || ''
  const activePriceIdx = Number(searchParams.get('price') || 0)

  useEffect(() => { getCategories().then(setCategories).catch(() => {}) }, [])

  const fetchProducts = useCallback(() => {
    setLoading(true)
    setError(null)
    const priceRange = PRICE_RANGES[activePriceIdx]
    getProducts({
      search: activeSearch || undefined,
      category: activeCategory || undefined,
      min_price: priceRange?.min ?? undefined,
      max_price: priceRange?.max ?? undefined,
      limit: 1000,
    })
      .then(setProducts)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [activeSearch, activeCategory, activePriceIdx])

  useEffect(() => { fetchProducts() }, [fetchProducts])

  const setParam = (key, val) => {
    const p = new URLSearchParams(searchParams)
    if (val) p.set(key, val); else p.delete(key)
    setSearchParams(p)
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setParam('search', searchInput)
  }

  const clearAll = () => {
    setSearchInput('')
    setSearchParams({})
  }

  const hasFilters = activeSearch || activeCategory || activePriceIdx > 0

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col gap-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Search size={22} className="text-brand-400" /> Explore Products
          </h1>
          <p className="text-gray-500 text-sm mt-1">Browse our full catalog · Every click improves your recommendations</p>
        </div>

        {/* Search bar */}
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="flex-1 relative">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search products, brands, features..."
              className="input-field pl-10 w-full"
            />
          </div>
          <button type="submit" className="btn-primary px-5">Search</button>
          {hasFilters && (
            <button type="button" onClick={clearAll}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-gray-400 hover:text-red-400 text-sm transition-all">
              <X size={14} /> Clear
            </button>
          )}
        </form>

        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          {/* Category filter */}
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setParam('category', '')}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${!activeCategory ? 'bg-brand-600 text-white border-brand-500' : 'bg-white/5 text-gray-400 border-white/10 hover:border-white/20'}`}
            >All</button>
            {categories.map((cat) => (
              <button key={cat}
                onClick={() => setParam('category', cat === activeCategory ? '' : cat)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${activeCategory === cat ? 'bg-brand-600 text-white border-brand-500' : 'bg-white/5 text-gray-400 border-white/10 hover:border-white/20'}`}
              >{cat}</button>
            ))}
          </div>
        </div>

        {/* Price filter */}
        <div className="flex gap-2 flex-wrap">
          {PRICE_RANGES.map((range, i) => (
            <button key={range.label}
              onClick={() => setParam('price', i > 0 ? String(i) : '')}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${activePriceIdx === i ? 'bg-purple-600 text-white border-purple-500' : 'bg-white/5 text-gray-400 border-white/10 hover:border-white/20'}`}
            >{range.label}</button>
          ))}
        </div>

        {/* Results count */}
        {!loading && (
          <p className="text-sm text-gray-500">
            {error ? '' : `${products.length} product${products.length !== 1 ? 's' : ''} found`}
            {activeSearch && <span className="text-gray-400"> for "<span className="text-white">{activeSearch}</span>"</span>}
          </p>
        )}

        {/* Grid */}
        {loading ? <GridSkeleton count={9} /> : error ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <p className="text-red-400">{error}</p>
          </div>
        ) : products.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
            <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
              <PackageSearch size={28} className="text-gray-600" />
            </div>
            <p className="text-gray-400 font-medium">No products found</p>
            <p className="text-sm text-gray-600">Try a different search term or clear the filters</p>
            <button onClick={clearAll} className="btn-secondary text-sm">Clear filters</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 animate-fade-in">
            {products.map((p) => (
              <ProductCard key={p.id} product={p} showScore={false} onCartUpdate={(c) => updateCartCount(c.item_count)} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
