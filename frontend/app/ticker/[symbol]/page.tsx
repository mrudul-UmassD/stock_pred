'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

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

export default function TickerDetailPage() {
  const params = useParams()
  const symbol = params?.symbol as string
  const [horizon, setHorizon] = useState<number>(5)
  const [latest, setLatest] = useState<Prediction | null>(null)
  const [history, setHistory] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (symbol) {
      fetchData()
    }
  }, [symbol, horizon])

  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch latest prediction
      const latestResponse = await fetch(
        `${API_URL}/api/predictions/latest?ticker=${symbol}&horizon=${horizon}`
      )
      if (latestResponse.ok) {
        const latestData = await latestResponse.json()
        setLatest(latestData)
      }

      // Fetch history
      const historyResponse = await fetch(
        `${API_URL}/api/predictions/history?ticker=${symbol}&horizon=${horizon}&limit=100`
      )
      if (historyResponse.ok) {
        const historyData = await historyResponse.json()
        setHistory(historyData.predictions)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case 'up':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20'
      case 'down':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20'
      default:
        return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800'
    }
  }

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`
  }

  // Prepare chart data
  const chartData = history
    .slice()
    .reverse()
    .map(p => ({
      time: new Date(p.ts).toLocaleDateString(),
      prob_up: p.prob_up * 100,
      prob_down: p.prob_down * 100,
      expected_return: p.expected_return * 100,
    }))

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {symbol} - Prediction Details
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Horizon Selector */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Prediction Horizon
          </label>
          <select
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value={1}>1 Day</option>
            <option value={5}>5 Days</option>
            <option value={20}>20 Days</option>
          </select>
        </div>

        {loading && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading data...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {!loading && !error && latest && (
          <div className="space-y-6">
            {/* Latest Prediction Card */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Latest Prediction
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Direction</p>
                  <span className={`inline-flex items-center px-4 py-2 rounded-full text-lg font-bold ${getDirectionColor(latest.direction)}`}>
                    {latest.direction.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Probability (Up/Down/Flat)</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    <span className="text-green-600">{formatPercent(latest.prob_up)}</span>
                    {' / '}
                    <span className="text-red-600">{formatPercent(latest.prob_down)}</span>
                    {' / '}
                    <span className="text-gray-600">{formatPercent(latest.prob_flat)}</span>
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Expected Return</p>
                  <p className={`text-2xl font-bold ${
                    latest.expected_return > 0 
                      ? 'text-green-600 dark:text-green-400' 
                      : latest.expected_return < 0 
                      ? 'text-red-600 dark:text-red-400' 
                      : 'text-gray-600 dark:text-gray-400'
                  }`}>
                    {latest.expected_return > 0 ? '+' : ''}{formatPercent(latest.expected_return)}
                  </p>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Last updated: {new Date(latest.ts).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Probability Chart */}
            {chartData.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Probability Trend
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis label={{ value: 'Probability (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="prob_up" stroke="#10b981" name="Up" strokeWidth={2} />
                    <Line type="monotone" dataKey="prob_down" stroke="#ef4444" name="Down" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Expected Return Chart */}
            {chartData.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Expected Return Trend
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis label={{ value: 'Expected Return (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="expected_return" stroke="#3b82f6" name="Expected Return" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Recent Predictions Table */}
            {history.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Recent Predictions
                  </h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          Timestamp
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          Direction
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          Prob Up
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          Prob Down
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          Expected Return
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {history.slice(0, 20).map((pred, idx) => (
                        <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                            {new Date(pred.ts).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 rounded text-xs font-medium ${getDirectionColor(pred.direction)}`}>
                              {pred.direction.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                            {formatPercent(pred.prob_up)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                            {formatPercent(pred.prob_down)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <span className={
                              pred.expected_return > 0 
                                ? 'text-green-600 dark:text-green-400' 
                                : pred.expected_return < 0 
                                ? 'text-red-600 dark:text-red-400' 
                                : 'text-gray-600 dark:text-gray-400'
                            }>
                              {pred.expected_return > 0 ? '+' : ''}{formatPercent(pred.expected_return)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {!loading && !error && !latest && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
            <p className="text-gray-600 dark:text-gray-400">
              No predictions found for {symbol} at horizon {horizon}.
            </p>
          </div>
        )}
      </main>
    </div>
  )
}
