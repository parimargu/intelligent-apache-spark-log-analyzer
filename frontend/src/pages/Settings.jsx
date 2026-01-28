import { useState } from 'react'
import { Save, Key, Brain, Database, Bell } from 'lucide-react'

export default function Settings() {
    const [settings, setSettings] = useState({
        llmProvider: 'openai',
        apiKey: '',
        database: 'sqlite',
        notifications: true
    })
    const [saved, setSaved] = useState(false)

    const handleSave = () => {
        // In a real app, this would call an API
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
    }

    return (
        <div className="fade-in">
            <div style={{ marginBottom: 'var(--spacing-xl)' }}>
                <h1>Settings</h1>
                <p style={{ marginTop: 'var(--spacing-xs)' }}>
                    Configure your Spark Log Analyzer
                </p>
            </div>

            {/* LLM Provider Settings */}
            <div className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
                <div className="card-header">
                    <h3 className="card-title">
                        <Brain size={20} style={{ color: 'var(--color-primary-light)' }} />
                        LLM Provider
                    </h3>
                </div>
                <div className="form-group">
                    <label className="form-label">Default Provider</label>
                    <select
                        className="form-input"
                        value={settings.llmProvider}
                        onChange={(e) => setSettings({ ...settings, llmProvider: e.target.value })}
                    >
                        <option value="openai">OpenAI (GPT-4)</option>
                        <option value="gemini">Google Gemini</option>
                        <option value="anthropic">Anthropic Claude</option>
                        <option value="groq">Groq</option>
                        <option value="openrouter">OpenRouter</option>
                        <option value="ollama">Ollama (Local)</option>
                    </select>
                </div>
                <div className="form-group">
                    <label className="form-label">
                        <Key size={14} style={{ marginRight: 4 }} />
                        API Key
                    </label>
                    <input
                        type="password"
                        className="form-input"
                        value={settings.apiKey}
                        onChange={(e) => setSettings({ ...settings, apiKey: e.target.value })}
                        placeholder="sk-..."
                    />
                    <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 4 }}>
                        Your API key is stored securely and never shared
                    </p>
                </div>
            </div>

            {/* Database Settings */}
            <div className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
                <div className="card-header">
                    <h3 className="card-title">
                        <Database size={20} style={{ color: 'var(--color-primary-light)' }} />
                        Database
                    </h3>
                </div>
                <div className="form-group">
                    <label className="form-label">Database Type</label>
                    <select
                        className="form-input"
                        value={settings.database}
                        onChange={(e) => setSettings({ ...settings, database: e.target.value })}
                    >
                        <option value="sqlite">SQLite (Development)</option>
                        <option value="postgresql">PostgreSQL (Production)</option>
                    </select>
                </div>
                <div className="alert alert-info">
                    <p style={{ fontSize: 'var(--font-size-sm)' }}>
                        Database settings are configured via environment variables.
                        See the <code>.env</code> file for configuration options.
                    </p>
                </div>
            </div>

            {/* Notifications */}
            <div className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
                <div className="card-header">
                    <h3 className="card-title">
                        <Bell size={20} style={{ color: 'var(--color-primary-light)' }} />
                        Notifications
                    </h3>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                        <div style={{ fontWeight: 500 }}>Enable Notifications</div>
                        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
                            Get notified when analysis is complete
                        </div>
                    </div>
                    <label style={{
                        position: 'relative',
                        display: 'inline-block',
                        width: 48,
                        height: 24,
                        cursor: 'pointer'
                    }}>
                        <input
                            type="checkbox"
                            checked={settings.notifications}
                            onChange={(e) => setSettings({ ...settings, notifications: e.target.checked })}
                            style={{ opacity: 0, width: 0, height: 0 }}
                        />
                        <span style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            background: settings.notifications ? 'var(--color-primary)' : 'var(--color-bg-tertiary)',
                            borderRadius: 'var(--radius-full)',
                            transition: 'background 0.2s'
                        }}>
                            <span style={{
                                position: 'absolute',
                                content: '',
                                height: 18,
                                width: 18,
                                left: settings.notifications ? 27 : 3,
                                bottom: 3,
                                background: 'white',
                                borderRadius: 'var(--radius-full)',
                                transition: 'left 0.2s'
                            }} />
                        </span>
                    </label>
                </div>
            </div>

            {/* Save Button */}
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button className="btn btn-primary btn-lg" onClick={handleSave}>
                    <Save size={20} />
                    {saved ? 'Saved!' : 'Save Settings'}
                </button>
            </div>
        </div>
    )
}
