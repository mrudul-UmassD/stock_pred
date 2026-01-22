'use client';

import { useState, useEffect } from 'react';
import LiveIndicator from '@/components/LiveIndicator';

interface Prediction {
  ts: string;
  ticker: string;
  horizon: number;
  direction: string;
  prob_up: number;
  prob_down: number;
  prob_flat: number;
  expected_return: number;
  model_version: string;
}

export default function AllStocksPage() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [horizon, setHorizon] = useState(5);
  const [sortBy, setSortBy] = useState('prob_up');
  const [order, setOrder] = useState('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDirection, setFilterDirection] = useState<'all' | 'up' | 'down' | 'flat'>('all');

  useEffect(() => {
    fetchPredictions();
  }, [horizon, sortBy, order]);

  const fetchPredictions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `http://localhost:8000/api/predictions/all?horizon=${horizon}&sort_by=${sortBy}&order=${order}&limit=1000`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch predictions');
      }
      
      const data = await response.json();
      setPredictions(data.predictions || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching predictions:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredPredictions = predictions.filter((pred) => {
    const matchesSearch = pred.ticker.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDirection = filterDirection === 'all' || pred.direction === filterDirection;
    return matchesSearch && matchesDirection;
  });

  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case 'up':
        return 'text-green-600 bg-green-50';
      case 'down':
        return 'text-red-600 bg-red-50';
      case 'flat':
        return 'text-yellow-600 bg-yellow-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getConfidence = (prob: number) => {
    if (prob >= 0.8) return 'High';
    if (prob >= 0.6) return 'Medium';
    return 'Low';
  };

  return (
    <div className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900">All US Stocks</h1>
            <p className="text-gray-600 mt-2">
              Predictions for {predictions.length} stocks
            </p>
          </div>
          <LiveIndicator />
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Ticker
              </label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="e.g., AAPL"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Horizon */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Horizon
              </label>
              <select
                value={horizon}
                onChange={(e) => setHorizon(Number(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value={1}>1 Day</option>
                <option value={5}>5 Days</option>
                <option value={20}>20 Days</option>
              </select>
            </div>

            {/* Direction Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Direction
              </label>
              <select
                value={filterDirection}
                onChange={(e) => setFilterDirection(e.target.value as any)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All</option>
                <option value="up">Up</option>
                <option value="down">Down</option>
                <option value="flat">Flat</option>
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="prob_up">Upside Probability</option>
                <option value="prob_down">Downside Probability</option>
                <option value="expected_return">Expected Return</option>
                <option value="ticker">Ticker</option>
              </select>
            </div>

            {/* Order */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Order
              </label>
              <select
                value={order}
                onChange={(e) => setOrder(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="desc">Highest First</option>
                <option value="asc">Lowest First</option>
              </select>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Showing {filteredPredictions.length} of {predictions.length} stocks
            </p>
            <button
              onClick={fetchPredictions}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Predictions Table */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-4">Loading predictions...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-600">{error}</p>
          </div>
        ) : filteredPredictions.length === 0 ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <p className="text-yellow-700">No predictions match your filters</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ticker
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Direction
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Upside
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Downside
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Flat
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Expected Return
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Confidence
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Updated
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredPredictions.map((pred) => {
                    const maxProb = Math.max(pred.prob_up, pred.prob_down, pred.prob_flat);
                    const confidence = getConfidence(maxProb);
                    
                    return (
                      <tr key={`${pred.ticker}-${pred.ts}`} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <a 
                            href={`/ticker/${pred.ticker}`}
                            className="text-blue-600 hover:text-blue-800 font-semibold"
                          >
                            {pred.ticker}
                          </a>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase ${getDirectionColor(pred.direction)}`}>
                            {pred.direction}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-green-600 font-medium">
                          {(pred.prob_up * 100).toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-red-600 font-medium">
                          {(pred.prob_down * 100).toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-yellow-600 font-medium">
                          {(pred.prob_flat * 100).toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <span className={pred.expected_return > 0 ? 'text-green-600' : 'text-red-600'}>
                            {pred.expected_return > 0 ? '+' : ''}{(pred.expected_return * 100).toFixed(2)}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-xs ${
                            confidence === 'High' ? 'text-green-600' :
                            confidence === 'Medium' ? 'text-yellow-600' :
                            'text-gray-600'
                          }`}>
                            {confidence}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(pred.ts).toLocaleString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
