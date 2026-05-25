import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap, Mail, Lock, User, MapPin, Eye, EyeOff, AlertCircle } from 'lucide-react'
import { signup, login } from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [form, setForm] = useState({ name: '', email: '', password: '', age: '', location: '' })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { login: authLogin } = useAuth()
  const navigate = useNavigate()

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      let data
      if (mode === 'signup') {
        data = await signup({
          name: form.name,
          email: form.email,
          password: form.password,
          age: form.age ? Number(form.age) : null,
          location: form.location || null,
        })
      } else {
        data = await login({ email: form.email, password: form.password })
      }
      authLogin(data)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/3 w-80 h-80 bg-purple-500/8 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md animate-slide-up">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center mb-4 shadow-lg shadow-brand-500/30">
            <Zap size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">RecoShop</h1>
          <p className="text-sm text-gray-500 mt-1">AI-powered product recommendations</p>
        </div>

        {/* Card */}
        <div className="glass-card p-8 border border-white/10">
          {/* Mode toggle */}
          <div className="flex rounded-xl bg-white/5 border border-white/10 p-1 mb-6">
            {['login', 'signup'].map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setError(null) }}
                className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${
                  mode === m
                    ? 'bg-brand-600 text-white shadow'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {m === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {mode === 'signup' && (
              <>
                <div className="relative">
                  <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                  <input required placeholder="Full name" value={form.name} onChange={set('name')}
                    className="input-field pl-10" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input placeholder="Age (optional)" type="number" min="13" max="120"
                    value={form.age} onChange={set('age')} className="input-field text-sm" />
                  <div className="relative">
                    <MapPin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input placeholder="City (optional)" value={form.location} onChange={set('location')}
                      className="input-field pl-9 text-sm" />
                  </div>
                </div>
              </>
            )}

            <div className="relative">
              <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
              <input required type="email" placeholder="Email address" value={form.email} onChange={set('email')}
                className="input-field pl-10" />
            </div>

            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
              <input required type={showPw ? 'text' : 'password'} placeholder="Password (min 6 chars)"
                value={form.password} onChange={set('password')} className="input-field pl-10 pr-10" />
              <button type="button" onClick={() => setShowPw((v) => !v)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {error && (
              <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                <AlertCircle size={15} className="shrink-0" />
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full py-3 disabled:opacity-60">
              {loading
                ? <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    {mode === 'login' ? 'Signing in...' : 'Creating account...'}
                  </span>
                : mode === 'login' ? 'Sign In' : 'Create Account'
              }
            </button>
          </form>

          {mode === 'login' && (
            <p className="text-center text-xs text-gray-500 mt-4">
              Demo Login: <span className="text-gray-300 font-semibold">john.doe@example.com</span> / <span className="text-gray-300 font-semibold">password123</span>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
