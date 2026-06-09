import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Users, Package, Activity, TrendingUp, Zap, ArrowRight,
  BarChart3, Brain, Target, Shield
} from 'lucide-react'
import { getHealth, getMetrics } from '../services/api'
import { LoadingSpinner } from '../components/LoadingSpinner'
import {
  RadialBarChart, RadialBar, ResponsiveContainer, Tooltip,
} from 'recharts'

const STRATEGY_INFO = [
  {
    title: 'Popularity',
    description: 'Cold-start baseline. Recommends globally trending products to new users.',
    icon: TrendingUp,
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10 border-yellow-500/20',
  },
  {
    title: 'Content-Based',
    description: 'TF-IDF + Cosine Similarity. Matches product text features for users with few interactions.',
    icon: Brain,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10 border-blue-500/20',
  },
  {
    title: 'Collaborative',
    description: 'User-User matrix cosine similarity. Finds similar users to predict preferences.',
    icon: Users,
    color: 'text-brand-400',
    bg: 'bg-brand-500/10 border-brand-500/20',
  },
  {
    title: 'SVD',
    description: 'Matrix Factorization. Discovers latent preference patterns as a fallback.',
    icon: Target,
    color: 'text-purple-400',
    bg: 'bg-purple-500/10 border-purple-500/20',
  },
]

function StatCard({ icon: Icon, label, value, color = 'text-brand-400', loading }) {
  return (
    <div className="stat-card">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color.replace('text-', 'bg-').replace('400', '500/10')} border border-white/10`}>
        <Icon size={20} className={color} />
      </div>
      {loading ? (
        <div className="skeleton h-8 w-20 rounded-lg" />
      ) : (
        <p className="text-3xl font-bold text-white tabular-nums">{value?.toLocaleString()}</p>
      )}
      <p className="text-sm text-gray-500">{label}</p>
    </div>
  )
}

function MetricGauge({ label, value, color }) {
  const pct = Math.round((value || 0) * 100)
  const data = [{ value: pct, fill: color }, { value: 100 - pct, fill: 'transparent' }]

  return (
    <div className="glass-card p-5 flex flex-col items-center gap-2">
      <div className="relative w-24 h-24">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            innerRadius="70%"
            outerRadius="100%"
            data={[{ value: pct, fill: color }]}
            startAngle={90}
            endAngle={-270}
          >
            <RadialBar dataKey="value" cornerRadius={6} background={{ fill: '#1f2937' }} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold text-white">{pct}%</span>
        </div>
      </div>
      <p className="text-sm text-gray-400 text-center">{label}</p>
    </div>
  )
}

export default function Dashboard() {
  const [health, setHealth] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [h, m] = await Promise.all([getHealth(), getMetrics(10)])
        setHealth(h)
        setMetrics(m)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex flex-col gap-10">
      {/* Hero */}
      <div className="text-center flex flex-col items-center gap-4 animate-fade-in">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-sm font-medium">
          <Zap size={14} />
          ML-Powered Recommendation Engine
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold text-white leading-tight">
          Smart Product{' '}
          <span className="text-gradient">Recommendations</span>
        </h1>
        <p className="max-w-2xl text-gray-400 text-lg leading-relaxed">
          A production-grade recommendation system using TF-IDF content filtering,
          collaborative filtering, matrix factorization, and popularity-based cold-start handling.
        </p>
        <div className="flex flex-wrap gap-3 justify-center">
          <Link to="/recommendations" className="btn-primary flex items-center gap-2">
            Get Recommendations <ArrowRight size={16} />
          </Link>
          <Link to="/similarity" className="btn-secondary flex items-center gap-2">
            Explore Similarity
          </Link>
        </div>
      </div>

      {/* System Stats */}
      <section>
        <h2 className="text-lg font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <BarChart3 size={18} className="text-brand-400" />
          System Overview
        </h2>

        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm mb-4">
            Backend connection error: {error}. Make sure the backend is running on port 8000.
          </div>
        )}

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={Users} label="Total Users" value={health?.total_users} color="text-blue-400" loading={loading} />
          <StatCard icon={Package} label="Products" value={health?.total_products} color="text-emerald-400" loading={loading} />
          <StatCard icon={Activity} label="Interactions" value={health?.total_interactions} color="text-purple-400" loading={loading} />
          <StatCard
            icon={Shield}
            label="ML Engine"
            value={health?.ml_engine_ready ? 'Ready' : 'Loading'}
            color={health?.ml_engine_ready ? 'text-emerald-400' : 'text-yellow-400'}
            loading={loading}
          />
        </div>
      </section>

      {/* Evaluation Metrics */}
      <section>
        <h2 className="text-lg font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <Target size={18} className="text-brand-400" />
          Model Performance (Hybrid Engine @ K=10)
        </h2>
        {loading ? (
          <div className="flex gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton h-40 flex-1 rounded-2xl" />
            ))}
          </div>
        ) : metrics ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <MetricGauge
              label={`Precision@${metrics.k}`}
              value={metrics.precision_at_k}
              color="#6366f1"
            />
            <MetricGauge
              label={`Recall@${metrics.k}`}
              value={metrics.recall_at_k}
              color="#8b5cf6"
            />
            <MetricGauge
              label="Hit Rate"
              value={metrics.hit_rate}
              color="#10b981"
            />
          </div>
        ) : null}
        {metrics && (
          <p className="text-xs text-gray-600 mt-3 text-center">
            Evaluated on {metrics.evaluated_users} users using leave-last-out split
          </p>
        )}
      </section>

      {/* Strategy Cards */}
      <section>
        <h2 className="text-lg font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <Brain size={18} className="text-brand-400" />
          Recommendation Strategies
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {STRATEGY_INFO.map(({ title, description, icon: Icon, color, bg }) => (
            <div key={title} className={`glass-card p-5 border ${bg}`}>
              <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center mb-3`}>
                <Icon size={20} className={color} />
              </div>
              <h3 className="font-bold text-white mb-1">{title}</h3>
              <p className="text-xs text-gray-500 leading-relaxed">{description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
