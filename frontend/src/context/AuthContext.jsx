import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const navigate = useNavigate()
    const [user, setUser] = useState(null)
    const [token, setToken] = useState(localStorage.getItem('token'))
    const [loading, setLoading] = useState(true)
    const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark')

    useEffect(() => {
        // Apply theme to document
        document.documentElement.setAttribute('data-theme', theme)
        localStorage.setItem('theme', theme)
    }, [theme])

    useEffect(() => {
        if (token) {
            fetchUser()
        } else {
            setLoading(false)
        }
    }, [token])

    const fetchUser = async () => {
        try {
            const response = await api.get('/auth/me')
            const userData = response.data
            setUser(userData)
            // Sync theme from user profile if available, otherwise keep local
            if (userData.theme) {
                setTheme(userData.theme)
            }
        } catch (error) {
            console.error('Failed to fetch user:', error)
            logout()
        } finally {
            setLoading(false)
        }
    }

    const login = async (email, password) => {
        const params = new URLSearchParams()
        params.append('username', email) // OAuth2 standard uses 'username' field, but we send email
        params.append('password', password)

        const response = await api.post('/auth/login', params, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        })
        const { access_token } = response.data

        localStorage.setItem('token', access_token)
        setToken(access_token)
        await fetchUser()

        return response.data
    }

    const register = async (userData) => {
        const response = await api.post('/auth/register', userData)
        return response.data
    }

    const logout = () => {
        localStorage.removeItem('token')
        setToken(null)
        setUser(null)
        navigate('/login')
    }

    const toggleTheme = async () => {
        const newTheme = theme === 'dark' ? 'light' : 'dark'
        setTheme(newTheme)

        // Update user preference if logged in
        if (user) {
            try {
                await api.put('/auth/me', { theme: newTheme })
                // Update local user object
                setUser({ ...user, theme: newTheme })
            } catch (err) {
                console.error('Failed to persist theme preference', err)
            }
        }
    }

    return (
        <AuthContext.Provider value={{ user, token, loading, theme, login, register, logout, toggleTheme }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
