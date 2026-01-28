import { useState, useEffect } from 'react'
import { BarChart3, PieChart, Download, Plus } from 'lucide-react'
import {
    PieChart as RechartPie, Pie, Cell, ResponsiveContainer, Tooltip,
    BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts'
import { reportApi } from '../services/api'
import { format } from 'date-fns'

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export default function Reports() {
    const [reports, setReports] = useState([])
    const [loading, setLoading] = useState(true)
    const [showCreate, setShowCreate] = useState(false)
    const [creating, setCreating] = useState(false)
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        report_type: 'summary'
    })

    useEffect(() => {
        fetchReports()
    }, [])

    const fetchReports = async () => {
        try {
            const response = await reportApi.list({ page_size: 50 })
            setReports(response.data.items)
        } catch (error) {
            console.error('Failed to fetch reports:', error)
        } finally {
            setLoading(false)
        }
    }

    const deleteReport = async (id) => {
        if (!window.confirm('Are you sure you want to delete this report?')) return
        try {
            await reportApi.delete(id)
            fetchReports()
        } catch (error) {
            alert('Failed to delete report')
        }
    }

    const createReport = async (e) => {
        e.preventDefault()
        setCreating(true)
        try {
            await reportApi.create(formData)
            setShowCreate(false)
            setFormData({ name: '', description: '', report_type: 'summary' })
            fetchReports()
        } catch (error) {
            alert('Failed to create report: ' + (error.response?.data?.detail || error.message))
        } finally {
            setCreating(false)
        }
    }

    if (loading) {
        return (
            <div className="fade-in">
                <h1 style={{ marginBottom: 'var(--spacing-xl)' }}>Reports</h1>
                <div className="skeleton" style={{ height: 300 }} />
            </div>
        )
    }

    return (
        <div className="fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-xl)' }}>
                <div>
                    <h1>Reports</h1>
                    <p style={{ marginTop: 'var(--spacing-xs)' }}>
                        Generated analysis reports and insights
                    </p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
                    <Plus size={20} />
                    New Report
                </button>
            </div>

            {/* Create Report Modal */}
            {showCreate && (
                <div className="card" style={{ marginBottom: 'var(--spacing-xl)' }}>
                    <h3 className="card-title" style={{ marginBottom: 'var(--spacing-md)' }}>Create New Report</h3>
                    <form onSubmit={createReport}>
                        <div className="form-group" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-md)' }}>
                            <div>
                                <label className="form-label">Report Name</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="Weekly Error Summary"
                                    required
                                />
                            </div>
                            <div>
                                <label className="form-label">Report Type</label>
                                <select
                                    className="form-input"
                                    value={formData.report_type}
                                    onChange={(e) => setFormData({ ...formData, report_type: e.target.value })}
                                >
                                    <option value="summary">Summary (Pie Chart)</option>
                                    <option value="detailed">Detailed (Category List)</option>
                                    <option value="trend">Trend Analysis (Bar Chart)</option>
                                </select>
                            </div>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Description</label>
                            <input
                                type="text"
                                className="form-input"
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                placeholder="Summary of errors from last week"
                            />
                        </div>
                        <div style={{ display: 'flex', gap: 'var(--spacing-sm)', justifyContent: 'flex-end' }}>
                            <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>
                                Cancel
                            </button>
                            <button type="submit" className="btn btn-primary" disabled={creating}>
                                {creating ? 'Creating...' : 'Create Report'}
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Reports List */}
            {reports.length === 0 ? (
                <div className="card" style={{ textAlign: 'center', padding: 'var(--spacing-2xl)' }}>
                    <BarChart3 size={48} style={{ color: 'var(--color-text-muted)', opacity: 0.5, marginBottom: 'var(--spacing-md)' }} />
                    <p style={{ color: 'var(--color-text-muted)' }}>No reports yet. Create your first report above.</p>
                </div>
            ) : (
                <div className="card-grid">
                    {reports.map((report) => {
                        const chartData = report.error_categories?.map((cat, idx) => ({
                            name: cat.category,
                            value: cat.count,
                            full: cat.category,
                            short: cat.category.length > 10 ? cat.category.substring(0, 8) + '...' : cat.category
                        })) || []

                        return (
                            <div key={report.id} className="card" style={{ display: 'flex', flexDirection: 'column' }}>
                                <div className="card-header">
                                    <h3 className="card-title" style={{ fontSize: 'var(--font-size-base)' }}>
                                        {report.name}
                                    </h3>
                                    <div style={{ display: 'flex', gap: 'var(--spacing-xs)', alignItems: 'center' }}>
                                        <span className={`badge badge-${report.report_type === 'detailed' ? 'info' :
                                            report.report_type === 'trend' ? 'warning' : 'primary'
                                            }`}>
                                            {report.report_type}
                                        </span>
                                        <button
                                            onClick={() => deleteReport(report.id)}
                                            style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', padding: '4px' }}
                                        >
                                            <Download size={14} style={{ transform: 'rotate(180deg)' }} />
                                        </button>
                                    </div>
                                </div>

                                {report.description && (
                                    <p style={{ fontSize: 'var(--font-size-sm)', marginBottom: 'var(--spacing-md)', color: 'var(--color-text-muted)' }}>
                                        {report.description}
                                    </p>
                                )}

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-md)' }}>
                                    <div className="metric-item">
                                        <div className="metric-label">Logs Analyzed</div>
                                        <div className="metric-value">{report.total_logs_analyzed}</div>
                                    </div>
                                    <div className="metric-item">
                                        <div className="metric-label">Total Errors</div>
                                        <div className="metric-value" style={{ color: 'var(--color-error)' }}>{report.total_errors}</div>
                                    </div>
                                </div>

                                <div style={{ flex: 1, minHeight: 180, marginTop: 'var(--spacing-sm)' }}>
                                    {report.report_type === 'summary' && chartData.length > 0 && (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <RechartPie>
                                                <Pie
                                                    data={chartData}
                                                    cx="50%"
                                                    cy="50%"
                                                    innerRadius={40}
                                                    outerRadius={70}
                                                    dataKey="value"
                                                >
                                                    {chartData.map((entry, index) => (
                                                        <Cell key={index} fill={COLORS[index % COLORS.length]} />
                                                    ))}
                                                </Pie>
                                                <Tooltip />
                                            </RechartPie>
                                        </ResponsiveContainer>
                                    )}

                                    {report.report_type === 'trend' && chartData.length > 0 && (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 20 }}>
                                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
                                                <XAxis
                                                    dataKey="short"
                                                    style={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
                                                    angle={-45}
                                                    textAnchor="end"
                                                />
                                                <YAxis style={{ fontSize: 10, fill: 'var(--color-text-muted)' }} />
                                                <Tooltip
                                                    contentStyle={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
                                                    labelStyle={{ color: 'var(--color-text-primary)' }}
                                                />
                                                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                                                    {chartData.map((entry, index) => (
                                                        <Cell key={index} fill={COLORS[index % COLORS.length]} />
                                                    ))}
                                                </Bar>
                                            </BarChart>
                                        </ResponsiveContainer>
                                    )}

                                    {report.report_type === 'detailed' && (
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xs)' }}>
                                            {report.error_categories?.slice(0, 5).map((cat, idx) => (
                                                <div key={idx} style={{ padding: '8px', background: 'var(--color-bg-primary)', borderRadius: '6px', fontSize: 'var(--font-size-xs)' }}>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                        <span style={{ fontWeight: 600 }}>{cat.category}</span>
                                                        <span style={{ color: 'var(--color-text-muted)' }}>{cat.count} ({cat.percentage}%)</span>
                                                    </div>
                                                    <div style={{ height: 4, background: 'var(--color-border)', borderRadius: 2 }}>
                                                        <div style={{
                                                            height: '100%',
                                                            width: `${cat.percentage}%`,
                                                            background: COLORS[idx % COLORS.length],
                                                            borderRadius: 2
                                                        }} />
                                                    </div>
                                                </div>
                                            ))}
                                            {report.error_categories?.length > 5 && (
                                                <div style={{ textAlign: 'center', fontSize: '10px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                                                    + {report.error_categories.length - 5} more categories
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>

                                <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', marginTop: 'var(--spacing-md)', display: 'flex', justifyContent: 'space-between' }}>
                                    <span>Created {format(new Date(report.created_at), 'MMM d, yyyy')}</span>
                                    <span>ID: #{report.id}</span>
                                </div>
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
