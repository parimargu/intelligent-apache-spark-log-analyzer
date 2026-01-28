import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
    FileText, AlertTriangle, AlertCircle,
    CheckCircle, Clock, TrendingUp, Brain
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { reportApi } from '../services/api'

export default function Dashboard() {
    const [summary, setSummary] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchDashboard()
    }, [])

    const fetchDashboard = async () => {
        try {
            const response = await reportApi.dashboard()
            setSummary(response.data)
        } catch (error) {
            console.error('Failed to fetch dashboard:', error)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="fade-in">
                <h1 style={{ marginBottom: 'var(--spacing-xl)' }}>Dashboard</h1>
                <div className="card-grid">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="card">
                            <div className="skeleton" style={{ height: 80 }} />
                        </div>
                    ))}
                </div>
            </div>
        )
    }

    const stats = [
        {
            icon: FileText,
            label: 'Total Log Files',
            value: summary?.total_log_files || 0,
            variant: 'default'
        },
        {
            icon: CheckCircle,
            label: 'Processed',
            value: summary?.processed_files || 0,
            variant: 'success'
        },
        {
            icon: AlertCircle,
            label: 'Total Errors',
            value: summary?.total_errors || 0,
            variant: 'error'
        },
        {
            icon: AlertTriangle,
            label: 'Total Warnings',
            value: summary?.total_warnings || 0,
            variant: 'warning'
        }
    ]

    return (
        <div className="fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-xl)' }}>
                <div>
                    <h1>Dashboard</h1>
                    <p style={{ marginTop: 'var(--spacing-xs)' }}>Monitor your Spark log analysis</p>
                </div>
                <Link to="/upload" className="btn btn-primary btn-lg">
                    <FileText size={20} />
                    Upload Logs
                </Link>
            </div>

            {/* Stats Grid */}
            <div className="card-grid" style={{ marginBottom: 'var(--spacing-xl)' }}>
                {stats.map(({ icon: Icon, label, value, variant }) => (
                    <div key={label} className="card">
                        <div className="stat-card">
                            <div className={`stat-icon ${variant}`}>
                                <Icon size={24} />
                            </div>
                            <div className="stat-content">
                                <div className="stat-value">{value.toLocaleString()}</div>
                                <div className="stat-label">{label}</div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Charts Row */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 'var(--spacing-lg)', marginBottom: 'var(--spacing-xl)' }}>
                {/* Error Trend Chart */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Error Trend (Last 7 Days)</h3>
                        <TrendingUp size={20} style={{ color: 'var(--color-text-muted)' }} />
                    </div>
                    <div style={{ height: 250 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={summary?.error_trend || []}>
                                <defs>
                                    <linearGradient id="errorGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis
                                    dataKey="date"
                                    tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }}
                                    tickFormatter={(value) => value.split('-').slice(1).join('/')}
                                />
                                <YAxis tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{
                                        background: 'var(--color-bg-secondary)',
                                        border: '1px solid var(--color-border)',
                                        borderRadius: 'var(--radius-md)'
                                    }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="count"
                                    stroke="#ef4444"
                                    fill="url(#errorGradient)"
                                    strokeWidth={2}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Top Error Categories */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Top Error Categories</h3>
                    </div>
                    <div>
                        {summary?.top_error_categories?.length > 0 ? (
                            summary.top_error_categories.map((cat, idx) => (
                                <div
                                    key={cat.category}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        padding: 'var(--spacing-sm) 0',
                                        borderBottom: idx < summary.top_error_categories.length - 1 ? '1px solid var(--color-border)' : 'none'
                                    }}
                                >
                                    <span style={{ color: 'var(--color-text-secondary)', textTransform: 'capitalize' }}>
                                        {cat.category}
                                    </span>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                                        <span className="badge badge-error">{cat.count}</span>
                                        <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>
                                            {cat.percentage}%
                                        </span>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <p style={{ textAlign: 'center', padding: 'var(--spacing-lg)', color: 'var(--color-text-muted)' }}>
                                No error categories found
                            </p>
                        )}
                    </div>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">Quick Actions</h3>
                </div>
                <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
                    <Link to="/upload" className="btn btn-secondary">
                        Upload New Logs
                    </Link>
                    <Link to="/analysis" className="btn btn-secondary">
                        <Brain size={16} />
                        Run AI Analysis
                    </Link>
                    <Link to="/reports" className="btn btn-secondary">
                        View Reports
                    </Link>
                </div>
            </div>
        </div>
    )
}
