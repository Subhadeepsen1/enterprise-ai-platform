import { useEffect, useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { getAnalyticsOverview, getAnalyticsTrends, getRiskDistribution } from '../services/api'
import { TrendingUp, ShieldAlert, BarChart3 } from 'lucide-react'

export default function AnalyticsPage() {
  const [trends, setTrends] = useState([])
  const [riskDist, setRiskDist] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getAnalyticsTrends(12), getRiskDistribution()])
      .then(([tr, rd]) => {
        setTrends(tr.data.trends)
        const dist = rd.data.risk_distribution
        setRiskDist([
          { name: 'Low (<20)', value: dist.low, fill: '#10b981' },
          { name: 'Medium (20-40)', value: dist.medium, fill: '#f59e0b' },
          { name: 'High (40-70)', value: dist.high, fill: '#f97316' },
          { name: 'Critical (>70)', value: dist.critical, fill: '#ef4444' },
        ])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading-overlay"><div className="spinner" /></div>

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Enterprise Analytics</h1>
        <p>In-depth analysis of processing volume, risk metrics, and system performance</p>
      </div>

      <div className="grid-2">
        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <div className="card-header"><div className="card-title"><TrendingUp size={14} /> 12-Month Processing Volume</div></div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trends}>
              <defs>
                <linearGradient id="gradVol" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="month" stroke="var(--text-muted)" fontSize={11} />
              <YAxis stroke="var(--text-muted)" fontSize={11} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }} />
              <Area type="monotone" dataKey="document_count" stroke="#3b82f6" fill="url(#gradVol)" strokeWidth={2} name="Documents Processed" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header"><div className="card-title"><ShieldAlert size={14} /> Risk Distribution Profile</div></div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={riskDist} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} />
              <YAxis stroke="var(--text-muted)" fontSize={11} />
              <Tooltip cursor={{ fill: 'var(--bg-surface)' }} contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header"><div className="card-title"><BarChart3 size={14} /> Average Risk Score Trend</div></div>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={trends}>
               <defs>
                <linearGradient id="gradRisk" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="month" stroke="var(--text-muted)" fontSize={11} />
              <YAxis domain={[0, 100]} stroke="var(--text-muted)" fontSize={11} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }} />
              <Area type="monotone" dataKey="avg_risk_score" stroke="#8b5cf6" fill="url(#gradRisk)" strokeWidth={2} name="Avg Risk Score" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
