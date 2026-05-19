import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  Home, Search, Star, ShoppingCart, Package, User, LogOut, Zap, BarChart3
} from 'lucide-react'

const navItems = [
  { to: '/', label: 'Home', icon: Home, exact: true },
  { to: '/explore', label: 'Explore', icon: Search },
  { to: '/recommendations', label: 'Recommendations', icon: Star },
  { to: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { to: '/orders', label: 'Orders', icon: Package },
  { to: '/profile', label: 'Profile', icon: User },
]

export default function Navbar() {
  const { user, logout, cartCount } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-white/10 bg-gray-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-lg">
              <Zap size={18} className="text-white" />
            </div>
            <div>
              <span className="font-bold text-gradient text-lg leading-none">RecoShop</span>
              <p className="text-xs text-gray-500 leading-none mt-0.5">AI Recommendations</p>
            </div>
          </div>

          {/* Nav links */}
          <div className="flex items-center gap-0.5">
            {navItems.map(({ to, label, icon: Icon, exact }) => (
              <NavLink
                key={to}
                to={to}
                end={exact}
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'active' : 'text-gray-400'}`
                }
              >
                <Icon size={15} />
                <span className="hidden md:inline text-xs">{label}</span>
              </NavLink>
            ))}

            {/* Cart with badge */}
            <NavLink
              to="/cart"
              className={({ isActive }) =>
                `nav-link relative ${isActive ? 'active' : 'text-gray-400'}`
              }
            >
              <ShoppingCart size={15} />
              <span className="hidden md:inline text-xs">Cart</span>
              {cartCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-brand-500 text-white text-xs rounded-full flex items-center justify-center font-bold leading-none">
                  {cartCount > 9 ? '9+' : cartCount}
                </span>
              )}
            </NavLink>
          </div>

          {/* Right: user + logout */}
          <div className="flex items-center gap-3">
            {user && (
              <span className="text-xs text-gray-400 hidden sm:block">
                Hi, <span className="text-white font-medium">{user.name?.split(' ')[0]}</span>
              </span>
            )}
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs text-gray-400 hover:text-red-400 hover:bg-red-500/10 border border-white/10 transition-all"
            >
              <LogOut size={13} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
