import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'

import Login from './pages/Login'
import Home from './pages/Home'
import ExploreProducts from './pages/ExploreProducts'
import ProductDetail from './pages/ProductDetail'
import Recommendations from './pages/Recommendations'
import Cart from './pages/Cart'
import Orders from './pages/Orders'
import Profile from './pages/Profile'
import Dashboard from './pages/Dashboard'

function AppRoutes() {
  const { logout } = useAuth()

  // Listen for 401 (token expired) events from the API layer
  useEffect(() => {
    const handler = () => logout()
    window.addEventListener('auth:expired', handler)
    return () => window.removeEventListener('auth:expired', handler)
  }, [logout])

  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<Login />} />

      {/* Protected — all require auth */}
      <Route path="/" element={<ProtectedRoute><Navbar /><Home /></ProtectedRoute>} />
      <Route path="/explore" element={<ProtectedRoute><Navbar /><ExploreProducts /></ProtectedRoute>} />
      <Route path="/products/:id" element={<ProtectedRoute><Navbar /><ProductDetail /></ProtectedRoute>} />
      <Route path="/recommendations" element={<ProtectedRoute><Navbar /><Recommendations /></ProtectedRoute>} />
      <Route path="/dashboard" element={<ProtectedRoute><Navbar /><Dashboard /></ProtectedRoute>} />
      <Route path="/cart" element={<ProtectedRoute><Navbar /><Cart /></ProtectedRoute>} />
      <Route path="/orders" element={<ProtectedRoute><Navbar /><Orders /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><Navbar /><Profile /></ProtectedRoute>} />

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col">
          <AppRoutes />
          <footer className="border-t border-white/5 py-5 mt-auto">
            <div className="max-w-7xl mx-auto px-4 text-center">
              <p className="text-xs text-gray-700">
                RecoShop · Smart Recommendation Engine · FastAPI + MongoDB + React ·{' '}
                <span className="text-brand-600">Hybrid ML Strategy</span>
              </p>
            </div>
          </footer>
        </div>
      </BrowserRouter>
    </AuthProvider>
  )
}
