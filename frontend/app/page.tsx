'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import PredictionTable from '@/components/PredictionTable'
import LiveIndicator from '@/components/LiveIndicator'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Prediction {
  ts: string
  ticker: string
  horizon: number
  direction: 'up' | 'down' | 'flat'
  prob_up: number
  prob_down: number
  prob_flat: number
  expected_return: number
  model_version: string
}

export default function Home() {
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [horizon, setHorizon] = useState<number>(5)
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [isLive, setIsLive] = useState<boolean>(false)
  const [lastUpdated, setLastUpdated] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch initial data
  useEffect(() => {
    fetchPredictions(horizon)
  }, [horizon])

  // Setup SSE connection for live updates
  useEffect(() => {
    if (!isLive) return

    const eventSource = new EventSource(`${API_URL}/api/stream?horizon=${horizon}`)

    eventSource.addEventListener('overview', (event) => {
      try {
        const data = JSON.parse(event.data)
        setPredictions(data.predictions)
        setLastUpdated(data.timestamp)
        setError(null)
      } catch (err) {
        console.error('Error parsing SSE data:', err)
      }
    })

    eventSource.addEventListener('error', (event) => {
      console.error('SSE error event:', event)
      setError('Connection error - retrying...')
    })

    eventSource.onerror = () => {
      setError('SSE connection failed')
    }

    return () => {
      eventSource.close()
    }
  }, [isLive, horizon])

  const fetchPredictions = async (selectedHorizon: number) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`${API_URL}/api/predictions/overview?horizon=${selectedHorizon}&limit=200`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setPredictions(data.predictions)
      setLastUpdated(new Date().toISOString())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch predictions')
      console.error('Error fetching predictions:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredPredictions = predictions.filter(p =>
    p.ticker.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const toggleLive = () => {
    setIsLive(!isLive)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              📈 Stock Prediction Dashboard
            </h1>
            <div className="flex gap-4">
              <Link
                href="/stocks"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                All Stocks
              </Link>
              <Link
                href="/ipos"
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Upcoming IPOs
              </Link>
              <Link
                href="/health"
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white flex items-center"
              >
                System Health
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Controls */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Horizon Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Prediction Horizon
              </label>
              <select
                value={horizon}
                onChange={(e) => setHorizon(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value={1}>1 Day</option>
                <option value={5}>5 Days</option>
                <option value={20}>20 Days</option>
              </select>
            </div>

            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search Ticker
              </label>
              <input
                type="text"
                placeholder="e.g., AAPL"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            {/* Live Updates Toggle */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Real-time Updates
              </label>
              <button
                onClick={toggleLive}
                className={`w-full px-4 py-2 rounded-md font-medium transition-colors ${
                  isLive
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white'
                }`}
              >
                {isLive ? '🟢 Live' : 'Connect Live'}
              </button>
            </div>
          </div>

          {/* Status Bar */}
          <div className="mt-4 flex justify-between items-center text-sm text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-4">
              <LiveIndicator isLive={isLive} />
              <span>
                {filteredPredictions.length} predictions
              </span>
            </div>
            {lastUpdated && (
              <span>
                Last updated: {new Date(lastUpdated).toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && predictions.length === 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading predictions...</p>
          </div>
        )}

        {/* Predictions Table */}
        {!loading && predictions.length === 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
            <p className="text-gray-600 dark:text-gray-400">
              No predictions available. Run the prediction script to generate data.
            </p>
            <code className="mt-2 block text-sm bg-gray-100 dark:bg-gray-700 p-2 rounded">
              python backend/scripts/predict.py --dummy
            </code>
          </div>
        )}

        {predictions.length > 0 && (
          <PredictionTable predictions={filteredPredictions} />
        )}
      </main>
    </div>
  )
}
