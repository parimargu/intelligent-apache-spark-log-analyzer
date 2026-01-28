import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
    ArrowLeft, FileText, Clock, AlertCircle,
    AlertTriangle, Info, Bug, Search, Brain
} from 'lucide-react'
import { logApi, analysisApi } from '../services/api'
import { format } from 'date-fns'

const levelIcons = {
    DEBUG: Bug,
    INFO: Info,
    WARN: AlertTriangle,
    ERROR: AlertCircle,
    FATAL: AlertCircle
}

const levelColors = {
    DEBUG: 'level-debug',
    INFO: 'level-info',
    WARN: 'level-warn',
    ERROR: 'level-error',
    FATAL: 'level-fatal'
}

export default function LogDetail() {
    const { id } = useParams()
    const [logFile, setLogFile] = useState(null)
    const [entries, setEntries] = useState([])
    const [loading, setLoading] = useState(true)
    const [entriesLoading, setEntriesLoading] = useState(false)
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [levelFilter, setLevelFilter] = useState('')
    const [search, setSearch] = useState('')
    const [analyzing, setAnalyzing] = useState(false)

    useEffect(() => {
        fetchLogFile()
    }, [id])

    useEffect(() => {
        if (logFile?.is_processed) {
            fetchEntries()
        }
    }, [id, page, levelFilter, logFile?.is_processed])

    const fetchLogFile = async () => {
        try {
            const response = await logApi.get(id)
            setLogFile(response.data)
        } catch (error) {
            console.error('Failed to fetch log file:', error)
        } finally {
            setLoading(false)
        }
    }

    const fetchEntries = async () => {
        setEntriesLoading(true)
        try {
            const params = { page, page_size: 50 }
            if (levelFilter) params.level = levelFilter
            if (search) params.search = search

            const response = await logApi.getEntries(id, params)
            setEntries(response.data.items)
            setTotalPages(response.data.total_pages)
        } catch (error) {
            console.error('Failed to fetch entries:', error)
        } finally {
            setEntriesLoading(false)
        }
    }

    const runAnalysis = async () => {
        setAnalyzing(true)
        try {
            await analysisApi.create({
                log_file_id: parseInt(id),
                analysis_type: 'full'
            })
            alert('Analysis started! Check the Analysis page for results.')
        } catch (error) {
            alert('Analysis failed: ' + (error.response?.data?.detail || error.message))
        } finally {
            setAnalyzing(false)
        }
    }

    const formatSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }

    if (loading) {
        return (
            <div className="fade-in">
                <div className="skeleton" style={{ height: 200 }} />
            </div>
        )
    }

    if (!logFile) {
        return (
            <div className="fade-in" style={{ textAlign: 'center', padding: 'var(--spacing-2xl)' }}>
                <AlertCircle size={48} style={{ color: 'var(--color-error)', marginBottom: 'var(--spacing-md)' }} />
                <h2>Log file not found</h2>
                <Link to="/logs" className="btn btn-primary" style={{ marginTop: 'var(--spacing-md)' }}>
                    Back to Logs
                </Link>
            </div>
        )
    }

    return (
        <div className="fade-in">
            {/* Header */}
            <div style={{ marginBottom: 'var(--spacing-xl)' }}>
                <Link to="/logs" style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--spacing-sm)', marginBottom: 'var(--spacing-md)' }}>
                    <ArrowLeft size={20} />
                    Back to Logs
                </Link>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                        <h1 style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                            <FileText size={32} style={{ color: 'var(--color-primary-light)' }} />
                            {logFile.original_filename}
                        </h1>
                        <p style={{ marginTop: 'var(--spacing-xs)', color: 'var(--color-text-muted)' }}>
                            Uploaded {format(new Date(logFile.created_at), 'MMMM d, yyyy \'at\' HH:mm')}
                        </p>
                    </div>
                    {logFile.is_processed && (
                        <button
                            className="btn btn-primary"
                            onClick={runAnalysis}
                            disabled={analyzing}
                        >
                            <Brain size={20} />
                            {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
                        </button>
                    )}
                </div>
            </div>

            {/* Stats */}
            <div className="card-grid" style={{ marginBottom: 'var(--spacing-xl)' }}>
                <div className="card">
                    <div className="stat-card">
                        <div className="stat-icon">
                            <FileText size={24} />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{formatSize(logFile.file_size)}</div>
                            <div className="stat-label">File Size</div>
                        </div>
                    </div>
                </div>
                <div className="card">
                    <div className="stat-card">
                        <div className="stat-icon success">
                            <Info size={24} />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{logFile.entry_count?.toLocaleString() || 0}</div>
                            <div className="stat-label">Total Entries</div>
                        </div>
                    </div>
                </div>
                <div className="card">
                    <div className="stat-card">
                        <div className="stat-icon error">
                            <AlertCircle size={24} />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{logFile.error_count?.toLocaleString() || 0}</div>
                            <div className="stat-label">Errors</div>
                        </div>
                    </div>
                </div>
                <div className="card">
                    <div className="stat-card">
                        <div className="stat-icon warning">
                            <AlertTriangle size={24} />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{logFile.warning_count?.toLocaleString() || 0}</div>
                            <div className="stat-label">Warnings</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Metadata */}
            <div className="card" style={{ marginBottom: 'var(--spacing-xl)' }}>
                <h3 className="card-title" style={{ marginBottom: 'var(--spacing-md)' }}>File Details</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--spacing-lg)' }}>
                    <div>
                        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>Source</div>
                        <div style={{ textTransform: 'capitalize' }}>{logFile.source?.replace('_', ' ')}</div>
                    </div>
                    <div>
                        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>Spark Mode</div>
                        <div style={{ textTransform: 'capitalize' }}>{logFile.spark_mode || 'Unknown'}</div>
                    </div>
                    <div>
                        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>Language</div>
                        <div style={{ textTransform: 'capitalize' }}>{logFile.detected_language || 'Unknown'}</div>
                    </div>
                    <div>
                        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>Status</div>
                        <div>
                            {logFile.is_processed ? (
                                <span className="badge badge-success">Processed</span>
                            ) : (
                                <span className="badge badge-warning">Pending</span>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Log Entries */}
            {logFile.is_processed && (
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Log Entries</h3>
                        <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
                            <select
                                className="form-input"
                                style={{ width: 'auto' }}
                                value={levelFilter}
                                onChange={(e) => { setLevelFilter(e.target.value); setPage(1); }}
                            >
                                <option value="">All Levels</option>
                                <option value="ERROR">Errors Only</option>
                                <option value="WARN">Warnings Only</option>
                                <option value="INFO">Info</option>
                                <option value="DEBUG">Debug</option>
                            </select>
                        </div>
                    </div>

                    {entriesLoading ? (
                        <div className="skeleton" style={{ height: 300 }} />
                    ) : entries.length === 0 ? (
                        <p style={{ textAlign: 'center', padding: 'var(--spacing-xl)', color: 'var(--color-text-muted)' }}>
                            No entries found
                        </p>
                    ) : (
                        <div style={{ maxHeight: 500, overflowY: 'auto' }}>
                            {entries.map((entry) => {
                                const Icon = levelIcons[entry.level] || Info
                                const colorClass = levelColors[entry.level] || ''

                                return (
                                    <div
                                        key={entry.id}
                                        style={{
                                            padding: 'var(--spacing-sm) var(--spacing-md)',
                                            borderBottom: '1px solid var(--color-border)',
                                            fontSize: 'var(--font-size-sm)',
                                            fontFamily: 'Monaco, Menlo, monospace'
                                        }}
                                    >
                                        <div style={{ display: 'flex', gap: 'var(--spacing-sm)', alignItems: 'flex-start' }}>
                                            <span style={{ color: 'var(--color-text-muted)', minWidth: 40 }}>
                                                {entry.line_number}
                                            </span>
                                            <Icon size={16} className={colorClass} style={{ marginTop: 2 }} />
                                            <span className={colorClass} style={{ minWidth: 50 }}>
                                                {entry.level || 'UNKNOWN'}
                                            </span>
                                            <span style={{ color: 'var(--color-text-muted)', minWidth: 80 }}>
                                                {entry.component || '-'}
                                            </span>
                                            <span style={{ flex: 1, wordBreak: 'break-all' }}>
                                                {entry.message}
                                            </span>
                                        </div>
                                        {entry.stack_trace && (
                                            <pre style={{
                                                marginTop: 'var(--spacing-xs)',
                                                marginLeft: 120,
                                                padding: 'var(--spacing-sm)',
                                                background: 'var(--color-bg-tertiary)',
                                                borderRadius: 'var(--radius-sm)',
                                                fontSize: 'var(--font-size-xs)',
                                                overflow: 'auto'
                                            }}>
                                                {entry.stack_trace}
                                            </pre>
                                        )}
                                    </div>
                                )
                            })}
                        </div>
                    )}

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div style={{
                            display: 'flex',
                            justifyContent: 'center',
                            gap: 'var(--spacing-md)',
                            padding: 'var(--spacing-md)',
                            borderTop: '1px solid var(--color-border)'
                        }}>
                            <button
                                className="btn btn-secondary"
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                            >
                                Previous
                            </button>
                            <span style={{ display: 'flex', alignItems: 'center', color: 'var(--color-text-muted)' }}>
                                Page {page} of {totalPages}
                            </span>
                            <button
                                className="btn btn-secondary"
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                            >
                                Next
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
