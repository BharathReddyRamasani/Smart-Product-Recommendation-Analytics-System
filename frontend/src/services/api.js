import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const stored = localStorage.getItem('auth_user')
  if (stored) {
    try {
      const { token } = JSON.parse(stored)
      if (token) config.headers.Authorization = `Bearer ${token}`
    } catch {}
  }
  return config
})

// Consistent error messages; 401 triggers logout via window event
api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      window.dispatchEvent(new CustomEvent('auth:expired'))
    }
    let msg = 'API Error'
    if (error.response?.data?.detail) {
      if (Array.isArray(error.response.data.detail)) {
        msg = error.response.data.detail.map(d => d.msg).join(', ')
      } else {
        msg = error.response.data.detail
      }
    } else if (error.message) {
      msg = error.message
    }
    return Promise.reject(new Error(msg))
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const signup = (data) => api.post('/api/v1/auth/signup', data).then((r) => r.data)
export const login = (data) => api.post('/api/v1/auth/login', data).then((r) => r.data)

// ── Products (public) ─────────────────────────────────────────────────────────
export const getProducts = (params = {}) =>
  api.get('/api/v1/products', { params }).then((r) => r.data)
export const getProduct = (id) => api.get(`/api/v1/products/${id}`).then((r) => r.data)
export const getPopularProducts = (k = 12, category = null) =>
  api.get('/api/v1/products/popular', { params: { k, ...(category && { category }) } }).then((r) => r.data)
export const getCategories = () => api.get('/api/v1/products/categories').then((r) => r.data)

// ── Home Feed (protected) ─────────────────────────────────────────────────────
export const getHomeFeed = () => api.get('/api/v1/home').then((r) => r.data)

// ── Recommendations (protected) ──────────────────────────────────────────────
export const getUserRecommendations = (k = 10, strategy = 'auto') =>
  api.get('/api/v1/recommend/user', { params: { k, strategy } }).then((r) => r.data)
export const getSimilarProducts = (productId, k = 8) =>
  api.get(`/api/v1/recommend/product/${productId}`, { params: { k } }).then((r) => r.data)
export const getMetrics = (k = 10) =>
  api.get('/api/v1/metrics', { params: { k } }).then((r) => r.data)

// ── Interactions (protected) ──────────────────────────────────────────────────
export const recordInteraction = (product_id, interaction_type, rating = null) =>
  api.post('/api/v1/interaction', {
    product_id,
    interaction_type,
    ...(rating !== null && { rating }),
  }).then((r) => r.data)

// ── Cart (protected) ──────────────────────────────────────────────────────────
export const getCart = () => api.get('/api/v1/cart').then((r) => r.data)
export const addToCart = (product_id, quantity = 1) =>
  api.post('/api/v1/cart/add', { product_id, quantity }).then((r) => r.data)
export const updateCartItem = (product_id, quantity) =>
  api.put(`/api/v1/cart/${product_id}`, { quantity }).then((r) => r.data)
export const removeFromCart = (product_id) =>
  api.delete(`/api/v1/cart/${product_id}`).then((r) => r.data)

// ── Orders (protected) ────────────────────────────────────────────────────────
export const placeOrder = () => api.post('/api/v1/orders/place').then((r) => r.data)
export const getOrders = (skip = 0, limit = 20) =>
  api.get('/api/v1/orders', { params: { skip, limit } }).then((r) => r.data)

// ── Profile (protected) ───────────────────────────────────────────────────────
export const getProfile = () => api.get('/api/v1/profile').then((r) => r.data)
export const updateProfile = (data) => api.put('/api/v1/profile', data).then((r) => r.data)

export const getHealth = () => api.get('/health').then((r) => r.data)

// ── Chat (protected) ──────────────────────────────────────────────────────────
export const sendChatMessage = (query, session_id = null) => 
  api.post('/api/v1/chat/', { query, session_id }).then((r) => r.data)
export default api
