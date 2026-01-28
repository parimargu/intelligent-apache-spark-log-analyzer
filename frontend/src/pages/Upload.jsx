import { useState, useRef, useCallback } from 'react'
import { Upload as UploadIcon, File, CheckCircle, XCircle, Loader } from 'lucide-react'
import { ingestionApi } from '../services/api'

export default function Upload() {
    const [files, setFiles] = useState([])
    const [uploading, setUploading] = useState(false)
    const [dragOver, setDragOver] = useState(false)
    const fileInputRef = useRef(null)

    const handleDragOver = useCallback((e) => {
        e.preventDefault()
        setDragOver(true)
    }, [])

    const handleDragLeave = useCallback((e) => {
        e.preventDefault()
        setDragOver(false)
    }, [])

    const handleDrop = useCallback((e) => {
        e.preventDefault()
        setDragOver(false)

        const droppedFiles = Array.from(e.dataTransfer.files)
        addFiles(droppedFiles)
    }, [])

    const handleFileSelect = (e) => {
        const selectedFiles = Array.from(e.target.files)
        addFiles(selectedFiles)
    }

    const addFiles = (newFiles) => {
        const validExtensions = ['.log', '.txt', '.gz', '.zip']

        const validatedFiles = newFiles.map((file) => {
            const ext = '.' + file.name.split('.').pop().toLowerCase()
            const isValid = validExtensions.includes(ext)

            return {
                file,
                name: file.name,
                size: file.size,
                status: isValid ? 'pending' : 'invalid',
                error: isValid ? null : 'Unsupported file type',
                progress: 0
            }
        })

        setFiles((prev) => [...prev, ...validatedFiles])
    }

    const removeFile = (index) => {
        setFiles((prev) => prev.filter((_, i) => i !== index))
    }

    const uploadFiles = async () => {
        const pendingFiles = files.filter((f) => f.status === 'pending')
        if (pendingFiles.length === 0) return

        setUploading(true)

        for (let i = 0; i < files.length; i++) {
            if (files[i].status !== 'pending') continue

            try {
                // Update status to uploading
                setFiles((prev) => prev.map((f, idx) =>
                    idx === i ? { ...f, status: 'uploading' } : f
                ))

                await ingestionApi.upload(files[i].file, (progress) => {
                    setFiles((prev) => prev.map((f, idx) =>
                        idx === i ? { ...f, progress } : f
                    ))
                })

                // Update status to success
                setFiles((prev) => prev.map((f, idx) =>
                    idx === i ? { ...f, status: 'success', progress: 100 } : f
                ))
            } catch (error) {
                // Update status to error
                setFiles((prev) => prev.map((f, idx) =>
                    idx === i ? {
                        ...f,
                        status: 'error',
                        error: error.response?.data?.detail || 'Upload failed'
                    } : f
                ))
            }
        }

        setUploading(false)
    }

    const formatSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }

    const StatusIcon = ({ status }) => {
        switch (status) {
            case 'success':
                return <CheckCircle size={20} style={{ color: 'var(--color-success)' }} />
            case 'error':
            case 'invalid':
                return <XCircle size={20} style={{ color: 'var(--color-error)' }} />
            case 'uploading':
                return <Loader size={20} className="pulse" style={{ color: 'var(--color-primary)' }} />
            default:
                return <File size={20} style={{ color: 'var(--color-text-muted)' }} />
        }
    }

    const pendingCount = files.filter((f) => f.status === 'pending').length
    const successCount = files.filter((f) => f.status === 'success').length

    return (
        <div className="fade-in">
            <div style={{ marginBottom: 'var(--spacing-xl)' }}>
                <h1>Upload Log Files</h1>
                <p style={{ marginTop: 'var(--spacing-xs)' }}>
                    Upload Apache Spark log files for AI-powered analysis
                </p>
            </div>

            {/* Upload Zone */}
            <div className="card" style={{ marginBottom: 'var(--spacing-xl)' }}>
                <div
                    className={`upload-zone ${dragOver ? 'dragover' : ''}`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        accept=".log,.txt,.gz,.zip"
                        onChange={handleFileSelect}
                        style={{ display: 'none' }}
                    />
                    <UploadIcon size={48} />
                    <h3>Drop files here or click to browse</h3>
                    <p>Supports .log, .txt, .gz, and .zip files (max 100MB each)</p>
                </div>
            </div>

            {/* File List */}
            {files.length > 0 && (
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Selected Files ({files.length})</h3>
                        <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
                            {successCount > 0 && (
                                <span className="badge badge-success">{successCount} uploaded</span>
                            )}
                            {pendingCount > 0 && (
                                <span className="badge badge-info">{pendingCount} pending</span>
                            )}
                        </div>
                    </div>

                    <div className="table-container">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>File</th>
                                    <th>Size</th>
                                    <th>Status</th>
                                    <th>Progress</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {files.map((file, index) => (
                                    <tr key={index}>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                                                <StatusIcon status={file.status} />
                                                <span>{file.name}</span>
                                            </div>
                                        </td>
                                        <td>{formatSize(file.size)}</td>
                                        <td>
                                            <span className={`badge badge-${file.status === 'success' ? 'success' :
                                                    file.status === 'error' || file.status === 'invalid' ? 'error' :
                                                        file.status === 'uploading' ? 'warning' : 'info'
                                                }`}>
                                                {file.status === 'invalid' ? 'Invalid' : file.status}
                                            </span>
                                        </td>
                                        <td style={{ width: 150 }}>
                                            {file.status === 'uploading' && (
                                                <div className="progress-bar">
                                                    <div className="progress-fill" style={{ width: `${file.progress}%` }} />
                                                </div>
                                            )}
                                            {file.error && (
                                                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-error)' }}>
                                                    {file.error}
                                                </span>
                                            )}
                                        </td>
                                        <td>
                                            {file.status !== 'uploading' && (
                                                <button
                                                    className="btn btn-icon btn-secondary"
                                                    onClick={() => removeFile(index)}
                                                >
                                                    <XCircle size={16} />
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {pendingCount > 0 && (
                        <div style={{ marginTop: 'var(--spacing-lg)', display: 'flex', justifyContent: 'flex-end' }}>
                            <button
                                className="btn btn-primary btn-lg"
                                onClick={uploadFiles}
                                disabled={uploading}
                            >
                                {uploading ? (
                                    <>
                                        <Loader size={20} className="pulse" />
                                        Uploading...
                                    </>
                                ) : (
                                    <>
                                        <UploadIcon size={20} />
                                        Upload {pendingCount} File{pendingCount > 1 ? 's' : ''}
                                    </>
                                )}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Info Card */}
            <div className="card" style={{ marginTop: 'var(--spacing-xl)' }}>
                <h4 style={{ marginBottom: 'var(--spacing-md)' }}>Supported Log Sources</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--spacing-lg)' }}>
                    <div>
                        <h5 style={{ color: 'var(--color-primary-light)', marginBottom: 'var(--spacing-xs)' }}>Spark Modes</h5>
                        <ul style={{ listStyle: 'none', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                            <li>• Spark Standalone</li>
                            <li>• Spark on YARN</li>
                            <li>• Spark on Kubernetes</li>
                        </ul>
                    </div>
                    <div>
                        <h5 style={{ color: 'var(--color-primary-light)', marginBottom: 'var(--spacing-xs)' }}>Languages</h5>
                        <ul style={{ listStyle: 'none', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                            <li>• Python (PySpark)</li>
                            <li>• Scala / Java</li>
                            <li>• Spark SQL / R</li>
                        </ul>
                    </div>
                    <div>
                        <h5 style={{ color: 'var(--color-primary-light)', marginBottom: 'var(--spacing-xs)' }}>File Formats</h5>
                        <ul style={{ listStyle: 'none', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                            <li>• Plain text (.log, .txt)</li>
                            <li>• Gzip compressed (.gz)</li>
                            <li>• Zip archives (.zip)</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    )
}
