import { useState, useEffect } from 'react'
import { useNavigate, Link, Navigate } from 'react-router-dom'
import { Zap, LogIn, UserPlus, Loader } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Login() {
    const navigate = useNavigate()
    const { login, register, token, user, loading: authLoading } = useAuth()
    const [mode, setMode] = useState('login')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    if (!authLoading && token && user) {
        return <Navigate to="/" replace />
    }
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        full_name: ''
    })

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            if (mode === 'login') {
                await login(formData.email, formData.password)
            } else {
                await register({
                    username: formData.username,
                    email: formData.email,
                    password: formData.password,
                    full_name: formData.full_name
                })
                await login(formData.email, formData.password)
            }
            navigate('/')
        } catch (err) {
            setError(err.response?.data?.detail || 'Authentication failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--spacing-xl)'
        }}>
            <div className="card fade-in" style={{ width: '100%', maxWidth: 420 }}>
                <div style={{ textAlign: 'center', marginBottom: 'var(--spacing-xl)' }}>
                    <div style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 'var(--spacing-sm)',
                        marginBottom: 'var(--spacing-md)'
                    }}>
                        <Zap size={32} style={{ color: 'var(--color-primary)' }} />
                        <span style={{
                            fontSize: 'var(--font-size-2xl)',
                            fontWeight: 700,
                            background: 'linear-gradient(135deg, var(--color-primary-light), var(--color-secondary))',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent'
                        }}>
                            Spark Analyzer
                        </span>
                    </div>
                    <p style={{ color: 'var(--color-text-muted)' }}>
                        {mode === 'login' ? 'Sign in to your account' : 'Create a new account'}
                    </p>
                </div>

                {error && (
                    <div className="alert alert-error" style={{ marginBottom: 'var(--spacing-md)' }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Email</label>
                        <input
                            type="email"
                            className="form-input"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            placeholder="name@example.com"
                            required
                        />
                    </div>

                    {mode === 'register' && (
                        <>
                            <div className="form-group">
                                <label className="form-label">Username</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    value={formData.username}
                                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                                    placeholder="Username"
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Full Name</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    value={formData.full_name}
                                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                                    placeholder="John Doe"
                                />
                            </div>
                        </>
                    )}

                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            type="password"
                            className="form-input"
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            placeholder="••••••••"
                            required
                            minLength={8}
                        />
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary btn-lg"
                        style={{ width: '100%', marginTop: 'var(--spacing-md)' }}
                        disabled={loading}
                    >
                        {loading ? (
                            <Loader size={20} className="pulse" />
                        ) : mode === 'login' ? (
                            <>
                                <LogIn size={20} />
                                Sign In
                            </>
                        ) : (
                            <>
                                <UserPlus size={20} />
                                Create Account
                            </>
                        )}
                    </button>
                </form>

                <div style={{
                    textAlign: 'center',
                    marginTop: 'var(--spacing-lg)',
                    paddingTop: 'var(--spacing-lg)',
                    borderTop: '1px solid var(--color-border)'
                }}>
                    {mode === 'login' ? (
                        <p style={{ color: 'var(--color-text-muted)' }}>
                            Don't have an account?{' '}
                            <button
                                type="button"
                                onClick={() => setMode('register')}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: 'var(--color-primary-light)',
                                    cursor: 'pointer',
                                    textDecoration: 'underline'
                                }}
                            >
                                Sign up
                            </button>
                        </p>
                    ) : (
                        <p style={{ color: 'var(--color-text-muted)' }}>
                            Already have an account?{' '}
                            <button
                                type="button"
                                onClick={() => setMode('login')}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: 'var(--color-primary-light)',
                                    cursor: 'pointer',
                                    textDecoration: 'underline'
                                }}
                            >
                                Sign in
                            </button>
                        </p>
                    )}
                </div>
            </div>
        </div>
    )
}
