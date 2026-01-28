import { useState, useEffect } from 'react'
import { Brain, Sparkles, Loader, Copy, Check, AlertCircle } from 'lucide-react'
import { analysisApi, logApi } from '../services/api'
import { format } from 'date-fns'

export default function Analysis() {
    const [analyses, setAnalyses] = useState([])
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedLog, setSelectedLog] = useState('')
    const [analysisType, setAnalysisType] = useState('full')
    const [analyzing, setAnalyzing] = useState(false)
    const [expandedId, setExpandedId] = useState(null)
    const [copiedId, setCopiedId] = useState(null)

    useEffect(() => {
        fetchData()
    }, [])

    const fetchData = async () => {
        try {
            const [analysesRes, logsRes] = await Promise.all([
                analysisApi.list({ page_size: 50 }),
                logApi.list({ is_processed: true, page_size: 100 })
            ])
            setAnalyses(analysesRes.data.items)
            setLogs(logsRes.data.items)
        } catch (error) {
            console.error('Failed to fetch data:', error)
        } finally {
            setLoading(false)
        }
    }

    const runAnalysis = async () => {
        if (!selectedLog) return

        setAnalyzing(true)
        try {
            await analysisApi.create({
                log_file_id: parseInt(selectedLog),
                analysis_type: analysisType
            })
            fetchData()
        } catch (error) {
            alert('Analysis failed: ' + (error.response?.data?.detail || error.message))
        } finally {
            setAnalyzing(false)
        }
    }

    const copyToClipboard = async (text, id) => {
        await navigator.clipboard.writeText(text)
        setCopiedId(id)
        setTimeout(() => setCopiedId(null), 2000)
    }

    const severityBadge = (severity) => {
        const variants = {
            low: 'badge-info',
            medium: 'badge-warning',
            high: 'badge-error',
            critical: 'badge-error'
        }
        return variants[severity] || 'badge-info'
    }

    if (loading) {
        return (
            <div className="fade-in">
                <h1 style={{ marginBottom: 'var(--spacing-xl)' }}>AI Analysis</h1>
                <div className="skeleton" style={{ height: 300 }} />
            </div>
        )
    }

    return (
        <div className="fade-in">
            <div style={{ marginBottom: 'var(--spacing-xl)' }}>
                <h1>AI Analysis</h1>
                <p style={{ marginTop: 'var(--spacing-xs)' }}>
                    AI-powered root cause analysis and recommendations
                </p>
            </div>

            {/* New Analysis */}
            <div className="card" style={{ marginBottom: 'var(--spacing-xl)' }}>
                <div className="card-header">
                    <h3 className="card-title">
                        <Brain size={20} style={{ color: 'var(--color-primary-light)' }} />
                        Run New Analysis
                    </h3>
                </div>
                <div style={{ display: 'flex', gap: 'var(--spacing-md)', alignItems: 'flex-end' }}>
                    <div style={{ flex: 1 }}>
                        <label className="form-label">Select Log File</label>
                        <select
                            className="form-input"
                            value={selectedLog}
                            onChange={(e) => setSelectedLog(e.target.value)}
                        >
                            <option value="">Choose a processed log file...</option>
                            {logs.map((log) => (
                                <option key={log.id} value={log.id}>
                                    {log.original_filename} ({log.error_count} errors)
                                </option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="form-label">Analysis Type</label>
                        <select
                            className="form-input"
                            value={analysisType}
                            onChange={(e) => setAnalysisType(e.target.value)}
                        >
                            <option value="full">Full Analysis</option>
                            <option value="root_cause">Root Cause</option>
                            <option value="memory_issues">Memory Issues</option>
                            <option value="performance">Performance</option>
                            <option value="config_optimization">Config Optimization</option>
                        </select>
                    </div>
                    <button
                        className="btn btn-primary"
                        onClick={runAnalysis}
                        disabled={!selectedLog || analyzing}
                    >
                        {analyzing ? (
                            <>
                                <Loader size={20} className="pulse" />
                                Analyzing...
                            </>
                        ) : (
                            <>
                                <Sparkles size={20} />
                                Analyze
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Analysis Results */}
            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">Analysis History</h3>
                    <span className="badge badge-info">{analyses.length} analyses</span>
                </div>

                {analyses.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 'var(--spacing-2xl)', color: 'var(--color-text-muted)' }}>
                        <Brain size={48} style={{ opacity: 0.5, marginBottom: 'var(--spacing-md)' }} />
                        <p>No analyses yet. Run your first AI analysis above.</p>
                    </div>
                ) : (
                    <div>
                        {analyses.map((analysis) => (
                            <div
                                key={analysis.id}
                                style={{
                                    borderBottom: '1px solid var(--color-border)',
                                    padding: 'var(--spacing-md)'
                                }}
                            >
                                <div
                                    style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        cursor: 'pointer'
                                    }}
                                    onClick={() => setExpandedId(expandedId === analysis.id ? null : analysis.id)}
                                >
                                    <div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                                            <Brain size={18} style={{ color: 'var(--color-primary-light)' }} />
                                            <span style={{ fontWeight: 500 }}>
                                                {analysis.analysis_type.replace('_', ' ').toUpperCase()}
                                            </span>
                                            <span className={`badge ${severityBadge(analysis.severity)}`}>
                                                {analysis.severity || 'N/A'}
                                            </span>
                                        </div>
                                        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginTop: 4 }}>
                                            {analysis.llm_provider} • {format(new Date(analysis.created_at), 'MMM d, HH:mm')}
                                            {analysis.processing_time_ms && ` • ${(analysis.processing_time_ms / 1000).toFixed(1)}s`}
                                        </div>
                                    </div>
                                    <AlertCircle
                                        size={20}
                                        style={{
                                            transform: expandedId === analysis.id ? 'rotate(180deg)' : 'rotate(0deg)',
                                            transition: 'transform 0.2s ease'
                                        }}
                                    />
                                </div>

                                {expandedId === analysis.id && (
                                    <div className="ai-panel" style={{ marginTop: 'var(--spacing-md)' }}>
                                        {analysis.summary && (
                                            <div style={{ marginBottom: 'var(--spacing-md)' }}>
                                                <h4 style={{ marginBottom: 'var(--spacing-sm)', fontSize: 'var(--font-size-sm)' }}>Summary</h4>
                                                <p className="ai-content">{analysis.summary}</p>
                                            </div>
                                        )}

                                        {analysis.root_cause && (
                                            <div style={{ marginBottom: 'var(--spacing-md)' }}>
                                                <h4 style={{ marginBottom: 'var(--spacing-sm)', fontSize: 'var(--font-size-sm)' }}>Root Cause</h4>
                                                <p className="ai-content">{analysis.root_cause}</p>
                                            </div>
                                        )}

                                        {analysis.recommendations?.length > 0 && (
                                            <div style={{ marginBottom: 'var(--spacing-md)' }}>
                                                <h4 style={{ marginBottom: 'var(--spacing-sm)', fontSize: 'var(--font-size-sm)' }}>Recommendations</h4>
                                                <ul style={{ paddingLeft: 'var(--spacing-lg)', color: 'var(--color-text-secondary)' }}>
                                                    {analysis.recommendations.map((rec, idx) => (
                                                        <li key={idx} style={{ marginBottom: 'var(--spacing-xs)' }}>
                                                            {typeof rec === 'string' ? rec : rec.description || rec.title}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {analysis.config_suggestions?.length > 0 && (
                                            <div>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-sm)' }}>
                                                    <h4 style={{ fontSize: 'var(--font-size-sm)' }}>Configuration Suggestions</h4>
                                                    <button
                                                        className="btn btn-secondary btn-icon"
                                                        onClick={() => copyToClipboard(
                                                            analysis.config_suggestions.map(c => `${c.config_key}=${c.suggested_value}`).join('\n'),
                                                            analysis.id
                                                        )}
                                                    >
                                                        {copiedId === analysis.id ? <Check size={16} /> : <Copy size={16} />}
                                                    </button>
                                                </div>
                                                <div style={{ background: 'var(--color-bg-tertiary)', padding: 'var(--spacing-sm)', borderRadius: 'var(--radius-sm)' }}>
                                                    {analysis.config_suggestions.map((config, idx) => (
                                                        <div key={idx} style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)', marginBottom: 4 }}>
                                                            <span style={{ color: 'var(--color-primary-light)' }}>{config.config_key}</span>
                                                            <span style={{ color: 'var(--color-text-muted)' }}>=</span>
                                                            <span style={{ color: 'var(--color-success)' }}>{config.suggested_value}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
