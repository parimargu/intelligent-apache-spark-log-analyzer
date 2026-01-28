import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FileText, Clock, CheckCircle, XCircle, Search, ChevronLeft, ChevronRight } from 'lucide-react'
import { logApi } from '../services/api'
import { format } from 'date-fns'

export default function Logs() {
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [search, setSearch] = useState('')
    const [filter, setFilter] = useState('all')

    useEffect(() => {
        fetchLogs()
    }, [page, filter])

    const fetchLogs = async () => {
        setLoading(true)
        try {
            const params = { page, page_size: 20 }
            if (filter !== 'all') {
                params.is_processed = filter === 'processed'
            }

            const response = await logApi.list(params)
            setLogs(response.data.items)
            setTotalPages(response.data.total_pages)
        } catch (error) {
            console.error('Failed to fetch logs:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleDelete = async (id) => {
        if (!confirm('Are you sure you want to delete this log file?')) return

        try {
            await logApi.delete(id)
            fetchLogs()
        } catch (error) {
            console.error('Failed to delete log:', error)
        }
    }

    const formatSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }

    const filteredLogs = logs.filter(log =>
        log.original_filename.toLowerCase().includes(search.toLowerCase())
    )

    return (
        <div className="fade-in">
            <div style={{ marginBottom: 'var(--spacing-xl)' }}>
                <h1>Log Files</h1>
                <p style={{ marginTop: 'var(--spacing-xs)' }}>
                    View and manage uploaded log files
                </p>
            </div>

            {/* Filters */}
            <div className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
                <div style={{ display: 'flex', gap: 'var(--spacing-md)', alignItems: 'center' }}>
                    <div style={{ flex: 1, position: 'relative' }}>
                        <Search
                            size={18}
                            style={{
                                position: 'absolute',
                                left: 12,
                                top: '50%',
                                transform: 'translateY(-50%)',
                                color: 'var(--color-text-muted)'
                            }}
                        />
                        <input
                            type="text"
                            className="form-input"
                            placeholder="Search by filename..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            style={{ paddingLeft: 40 }}
                        />
                    </div>
                    <select
                        className="form-input"
                        style={{ width: 'auto' }}
                        value={filter}
                        onChange={(e) => { setFilter(e.target.value); setPage(1); }}
                    >
                        <option value="all">All Files</option>
                        <option value="processed">Processed</option>
                        <option value="pending">Pending</option>
                    </select>
                </div>
            </div>

            {/* Log Table */}
            <div className="card">
                {loading ? (
                    <div style={{ padding: 'var(--spacing-xl)', textAlign: 'center' }}>
                        <div className="skeleton" style={{ height: 200 }} />
                    </div>
                ) : filteredLogs.length === 0 ? (
                    <div style={{ padding: 'var(--spacing-xl)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                        <FileText size={48} style={{ marginBottom: 'var(--spacing-md)', opacity: 0.5 }} />
                        <p>No log files found</p>
                        <Link to="/upload" className="btn btn-primary" style={{ marginTop: 'var(--spacing-md)' }}>
                            Upload Logs
                        </Link>
                    </div>
                ) : (
                    <>
                        <div className="table-container">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Filename</th>
                                        <th>Size</th>
                                        <th>Source</th>
                                        <th>Status</th>
                                        <th>Entries</th>
                                        <th>Errors</th>
                                        <th>Uploaded</th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredLogs.map((log) => (
                                        <tr key={log.id}>
                                            <td>
                                                <Link
                                                    to={`/logs/${log.id}`}
                                                    style={{
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        gap: 'var(--spacing-sm)',
                                                        color: 'var(--color-text-primary)'
                                                    }}
                                                >
                                                    <FileText size={18} style={{ color: 'var(--color-primary-light)' }} />
                                                    {log.original_filename}
                                                </Link>
                                            </td>
                                            <td>{formatSize(log.file_size)}</td>
                                            <td>
                                                <span className="badge badge-info" style={{ textTransform: 'capitalize' }}>
                                                    {log.source.replace('_', ' ')}
                                                </span>
                                            </td>
                                            <td>
                                                {log.is_processed ? (
                                                    <span className="badge badge-success">
                                                        <CheckCircle size={12} style={{ marginRight: 4 }} />
                                                        Processed
                                                    </span>
                                                ) : (
                                                    <span className="badge badge-warning">
                                                        <Clock size={12} style={{ marginRight: 4 }} />
                                                        Pending
                                                    </span>
                                                )}
                                            </td>
                                            <td>{log.entry_count?.toLocaleString() || '-'}</td>
                                            <td>
                                                {log.error_count > 0 ? (
                                                    <span style={{ color: 'var(--color-error)' }}>{log.error_count}</span>
                                                ) : (
                                                    <span style={{ color: 'var(--color-text-muted)' }}>0</span>
                                                )}
                                            </td>
                                            <td style={{ color: 'var(--color-text-muted)' }}>
                                                {format(new Date(log.created_at), 'MMM d, yyyy HH:mm')}
                                            </td>
                                            <td>
                                                <button
                                                    className="btn btn-icon btn-secondary"
                                                    onClick={() => handleDelete(log.id)}
                                                    title="Delete"
                                                >
                                                    <XCircle size={16} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Pagination */}
                        {totalPages > 1 && (
                            <div style={{
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                                gap: 'var(--spacing-md)',
                                marginTop: 'var(--spacing-lg)'
                            }}>
                                <button
                                    className="btn btn-secondary btn-icon"
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                >
                                    <ChevronLeft size={20} />
                                </button>
                                <span style={{ color: 'var(--color-text-secondary)' }}>
                                    Page {page} of {totalPages}
                                </span>
                                <button
                                    className="btn btn-secondary btn-icon"
                                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                    disabled={page === totalPages}
                                >
                                    <ChevronRight size={20} />
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
