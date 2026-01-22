'use client';

import { useState, useEffect } from 'react';
import LiveIndicator from '@/components/LiveIndicator';

interface IPO {
  symbol: string;
  company_name: string;
  ipo_date: string;
  price_range_low: number;
  price_range_high: number;
  expected_price: number;
  shares_offered: number;
  market_cap_estimate: number;
  sector: string;
  exchange: string;
  underwriters: string;
  profitability: {
    prediction: string;
    confidence: string;
    score: number;
    factors: {
      sector_strength: boolean;
      market_cap_adequate: boolean;
      price_range_tight: boolean;
      premium_underwriters: boolean;
    };
  };
}

export default function IPOsPage() {
  const [ipos, setIpos] = useState<IPO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [daysAhead, setDaysAhead] = useState(7);
  const [sortBy, setSortBy] = useState<'score' | 'date' | 'market_cap'>('score');

  useEffect(() => {
    fetchIPOs();
  }, [daysAhead]);

  const fetchIPOs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`http://localhost:8000/api/ipos/upcoming?days_ahead=${daysAhead}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch IPOs');
      }
      
      const data = await response.json();
      setIpos(data.ipos || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching IPOs:', err);
    } finally {
      setLoading(false);
    }
  };

  const sortedIPOs = [...ipos].sort((a, b) => {
    if (sortBy === 'score') {
      return b.profitability.score - a.profitability.score;
    } else if (sortBy === 'date') {
      return new Date(a.ipo_date).getTime() - new Date(b.ipo_date).getTime();
    } else {
      return b.market_cap_estimate - a.market_cap_estimate;
    }
  });

  const getProfitabilityColor = (prediction: string) => {
    switch (prediction) {
      case 'Highly Profitable':
        return 'text-green-600 bg-green-50';
      case 'Likely Profitable':
        return 'text-green-500 bg-green-50';
      case 'Neutral':
        return 'text-yellow-600 bg-yellow-50';
      case 'Risky':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const formatMarketCap = (value: number) => {
    if (value >= 1e9) {
      return `$${(value / 1e9).toFixed(2)}B`;
    }
    return `$${(value / 1e6).toFixed(0)}M`;
  };

  return (
    <div className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900">Upcoming IPOs</h1>
            <p className="text-gray-600 mt-2">
              Track and analyze upcoming initial public offerings
            </p>
          </div>
          <LiveIndicator isLive={false} />
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Look Ahead Days
              </label>
              <select
                value={daysAhead}
                onChange={(e) => setDaysAhead(Number(e.target.value))}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value={7}>7 days</option>
                <option value={14}>14 days</option>
                <option value={30}>30 days</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="score">Profitability Score</option>
                <option value="date">IPO Date</option>
                <option value="market_cap">Market Cap</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={fetchIPOs}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* IPO Cards */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-4">Loading IPOs...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-600">{error}</p>
          </div>
        ) : sortedIPOs.length === 0 ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <p className="text-yellow-700">No upcoming IPOs found for the next {daysAhead} days</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {sortedIPOs.map((ipo) => (
              <div key={ipo.symbol} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-900">{ipo.company_name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">
                        {ipo.symbol}
                      </span>
                      <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded">
                        {ipo.exchange}
                      </span>
                      <span className="text-gray-600 text-sm">{ipo.sector}</span>
                    </div>
                  </div>
                  <div className={`px-4 py-2 rounded-lg font-semibold text-sm ${getProfitabilityColor(ipo.profitability.prediction)}`}>
                    Score: {ipo.profitability.score}
                  </div>
                </div>

                {/* Details */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-gray-600">IPO Date</p>
                    <p className="font-semibold text-gray-900">
                      {new Date(ipo.ipo_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Price Range</p>
                    <p className="font-semibold text-gray-900">
                      ${ipo.price_range_low.toFixed(2)} - ${ipo.price_range_high.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Expected Price</p>
                    <p className="font-semibold text-gray-900">${ipo.expected_price.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Market Cap Est.</p>
                    <p className="font-semibold text-gray-900">{formatMarketCap(ipo.market_cap_estimate)}</p>
                  </div>
                </div>

                {/* Profitability Prediction */}
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-900">Profitability Analysis</h4>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getProfitabilityColor(ipo.profitability.prediction)}`}>
                      {ipo.profitability.prediction}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span className={ipo.profitability.factors.sector_strength ? 'text-green-600' : 'text-gray-400'}>
                        {ipo.profitability.factors.sector_strength ? '✓' : '○'}
                      </span>
                      <span className="text-gray-600">Strong Sector</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={ipo.profitability.factors.market_cap_adequate ? 'text-green-600' : 'text-gray-400'}>
                        {ipo.profitability.factors.market_cap_adequate ? '✓' : '○'}
                      </span>
                      <span className="text-gray-600">Adequate Size</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={ipo.profitability.factors.price_range_tight ? 'text-green-600' : 'text-gray-400'}>
                        {ipo.profitability.factors.price_range_tight ? '✓' : '○'}
                      </span>
                      <span className="text-gray-600">Tight Pricing</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={ipo.profitability.factors.premium_underwriters ? 'text-green-600' : 'text-gray-400'}>
                        {ipo.profitability.factors.premium_underwriters ? '✓' : '○'}
                      </span>
                      <span className="text-gray-600">Top Underwriters</span>
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 mt-3">
                    Underwriters: {ipo.underwriters}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Info Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>
            IPO profitability predictions are based on historical patterns and multiple factors.
            Not financial advice - conduct your own research.
          </p>
        </div>
      </div>
    </div>
  );
}
