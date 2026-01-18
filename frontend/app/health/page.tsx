'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface HealthData {
  status: string
  time: string
  db_ok: boolean
  model_version: string
}

export default function HealthPage() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setHealth(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health status')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    return status === 'healthy' ? 'text-green-600' : 'text-red-600'
  }

  const getStatusBg = (status: string) => {
    return status === 'healthy' 
      ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
      : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              System Health
            </h1>
            <Link
              href="/"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && !health && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Checking system health...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
              Connection Error
            </h3>
            <p className="text-red-700 dark:text-red-300">{error}</p>
            <p className="mt-4 text-sm text-red-600 dark:text-red-400">
              Make sure the backend server is running on {API_URL}
            </p>
          </div>
        )}

        {health && (
          <div className="space-y-6">
            {/* Overall Status */}
            <div className={`border-2 rounded-lg p-6 ${getStatusBg(health.status)}`}>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    System Status
                  </h2>
                  <p className={`text-4xl font-bold mt-2 ${getStatusColor(health.status)}`}>
                    {health.status === 'healthy' ? '✓ Healthy' : '✗ Unhealthy'}
                  </p>
                </div>
                <div className={`w-20 h-20 rounded-full flex items-center justify-center text-4xl ${
                  health.status === 'healthy' 
                    ? 'bg-green-100 dark:bg-green-900/40' 
                    : 'bg-red-100 dark:bg-red-900/40'
                }`}>
                  {health.status === 'healthy' ? '✓' : '✗'}
                </div>
              </div>
            </div>

            {/* Component Status */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Components
                </h3>
              </div>
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {/* Database */}
                <div className="px-6 py-4 flex justify-between items-center">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Database</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">SQLite predictions storage</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${
                      health.db_ok ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <span className={`font-medium ${
                      health.db_ok ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                    }`}>
                      {health.db_ok ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                </div>

                {/* Model */}
                <div className="px-6 py-4 flex justify-between items-center">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Model</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">XGBoost classifier</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${
                      health.model_version !== 'not_trained' ? 'bg-green-500' : 'bg-yellow-500'
                    }`} />
                    <span className="font-medium text-gray-700 dark:text-gray-300">
                      {health.model_version}
                    </span>
                  </div>
                </div>

                {/* API */}
                <div className="px-6 py-4 flex justify-between items-center">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">API Server</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">FastAPI backend</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                    <span className="font-medium text-green-600 dark:text-green-400">
                      Running
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* System Information */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                System Information
              </h3>
              <dl className="grid grid-cols-1 gap-4">
                <div className="flex justify-between">
                  <dt className="text-gray-600 dark:text-gray-400">Server Time</dt>
                  <dd className="font-mono text-gray-900 dark:text-white">
                    {new Date(health.time).toLocaleString()}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600 dark:text-gray-400">API URL</dt>
                  <dd className="font-mono text-gray-900 dark:text-white">
                    {API_URL}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600 dark:text-gray-400">Last Checked</dt>
                  <dd className="font-mono text-gray-900 dark:text-white">
                    {new Date().toLocaleTimeString()}
                  </dd>
                </div>
              </dl>
            </div>

            {/* Actions */}
            {health.model_version === 'not_trained' && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
                  Model Not Trained
                </h3>
                <p className="text-yellow-700 dark:text-yellow-300 mb-4">
                  The prediction model has not been trained yet. Run the training notebook to generate the model.
                </p>
                <code className="block text-sm bg-yellow-100 dark:bg-yellow-900/40 p-3 rounded font-mono">
                  jupyter notebook notebooks/train.ipynb
                </code>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
