import { Outlet, NavLink, Navigate } from 'react-router-dom'
import {
    LayoutDashboard, Upload, FileText, Brain,
    BarChart3, Settings, LogOut, Zap, Sun, Moon
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/upload', icon: Upload, label: 'Upload Logs' },
    { path: '/logs', icon: FileText, label: 'Log Files' },
    { path: '/analysis', icon: Brain, label: 'AI Analysis' },
    { path: '/reports', icon: BarChart3, label: 'Reports' },
    { path: '/settings', icon: Settings, label: 'Settings' }
]

export default function Layout() {
    const { user, token, logout, theme, toggleTheme, loading } = useAuth()

    if (!loading && !token) {
        return <Navigate to="/login" replace />
    }

    if (loading) {
        return (
            <div style={{
                height: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'var(--color-bg-primary)',
                color: 'var(--color-text-primary)'
            }}>
                <div className="skeleton" style={{ width: '200px', height: '20px' }}>Loading...</div>
            </div>
        )
    }

    return (
        <div className="app-layout">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <div className="sidebar-logo">
                        <Zap />
                        <span>Spark Analyzer</span>
                    </div>
                </div>

                <nav className="sidebar-nav">
                    {navItems.map(({ path, icon: Icon, label }) => (
                        <NavLink
                            key={path}
                            to={path}
                            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                            end={path === '/'}
                        >
                            <Icon size={20} />
                            <span>{label}</span>
                        </NavLink>
                    ))}
                </nav>

                <div style={{ padding: 'var(--spacing-md)', borderTop: '1px solid var(--color-border)' }}>
                    {user && (
                        <div style={{ marginBottom: 'var(--spacing-md)', fontSize: 'var(--font-size-sm)' }}>
                            <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                                {user.full_name || user.username}
                            </div>
                            <div style={{
                                color: 'var(--color-text-muted)',
                                fontSize: 'var(--font-size-xs)',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                marginTop: '2px'
                            }}>
                                {user.role}
                            </div>
                        </div>
                    )}

                    <button
                        className="btn btn-secondary"
                        style={{ width: '100%', marginBottom: 'var(--spacing-sm)', justifyContent: 'space-between' }}
                        onClick={toggleTheme}
                    >
                        <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
                            <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
                        </span>
                    </button>

                    <button className="btn btn-secondary" style={{ width: '100%' }} onClick={logout}>
                        <LogOut size={16} />
                        <span>Logout</span>
                    </button>
                </div>
            </aside>

            <main className="main-content">
                <Outlet />
            </main>
        </div>
    )
}
