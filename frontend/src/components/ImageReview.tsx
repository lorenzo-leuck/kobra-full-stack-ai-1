import { useState, useEffect } from 'react';
import { ArrowLeft, Filter, Grid, List, CheckCircle, XCircle, ExternalLink, Star, BarChart3 } from 'lucide-react';
import StatusBadge from './StatusBadge';
import ScoreBar from './ScoreBar';
import LoadingSpinner from './LoadingSpinner';
import ThemeToggle from './ThemeToggle';

interface Pin {
  _id: string;
  image_url: string;
  pin_url: string;
  title: string;
  description: string;
  match_score: number;
  status: 'approved' | 'disqualified';
  ai_explanation: string;
  metadata: {
    collected_at: string;
  };
}

interface ImageReviewProps {
  promptId: string;
  originalPrompt: string;
  onBack: () => void;
}

export default function ImageReview({ promptId, originalPrompt, onBack }: ImageReviewProps) {
  const [pins, setPins] = useState<Pin[]>([]);
  const [filteredPins, setFilteredPins] = useState<Pin[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [statusFilter, setStatusFilter] = useState<'all' | 'approved' | 'disqualified'>('all');
  const [scoreThreshold, setScoreThreshold] = useState(0.0);

  useEffect(() => {
    // TODO: Replace with actual API call
    // const fetchPins = async () => {
    //   try {
    //     const response = await fetch(`/api/prompts/${promptId}/pins`);
    //     const data = await response.json();
    //     setPins(data.pins);
    //   } catch (error) {
    //     console.error('Failed to fetch pins:', error);
    //   } finally {
    //     setLoading(false);
    //   }
    // };

    // Simulate API response with mock data
    const mockPins: Pin[] = [
      {
        _id: '1',
        image_url: 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400',
        pin_url: 'https://pinterest.com/pin/1',
        title: 'Modern Industrial Home Office Setup',
        description: 'Clean lines and industrial elements create the perfect workspace',
        match_score: 0.92,
        status: 'approved',
        ai_explanation: 'Excellent match with industrial elements, clean desk setup, and modern aesthetic.',
        metadata: { collected_at: new Date().toISOString() }
      },
      {
        _id: '2',
        image_url: 'https://images.unsplash.com/photo-1541558869434-2840d308329a?w=400',
        pin_url: 'https://pinterest.com/pin/2',
        title: 'Cozy Reading Nook with Industrial Touches',
        description: 'Warm lighting and metal accents in a comfortable corner',
        match_score: 0.78,
        status: 'approved',
        ai_explanation: 'Good match with cozy atmosphere and some industrial elements like metal fixtures.',
        metadata: { collected_at: new Date().toISOString() }
      },
      {
        _id: '3',
        image_url: 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400',
        pin_url: 'https://pinterest.com/pin/3',
        title: 'Bright Modern Kitchen',
        description: 'All white kitchen with marble countertops',
        match_score: 0.23,
        status: 'disqualified',
        ai_explanation: 'Does not match the industrial home office criteria - this is a kitchen with no industrial elements.',
        metadata: { collected_at: new Date().toISOString() }
      },
      {
        _id: '4',
        image_url: 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400',
        pin_url: 'https://pinterest.com/pin/4',
        title: 'Industrial Desk with Exposed Brick',
        description: 'Raw materials and functional design for productivity',
        match_score: 0.95,
        status: 'approved',
        ai_explanation: 'Perfect match with exposed brick, industrial desk, and office functionality.',
        metadata: { collected_at: new Date().toISOString() }
      },
      {
        _id: '5',
        image_url: 'https://images.unsplash.com/photo-1541558869434-2840d308329a?w=400',
        pin_url: 'https://pinterest.com/pin/5',
        title: 'Vintage Office Chair',
        description: 'Classic leather chair with metal frame',
        match_score: 0.67,
        status: 'approved',
        ai_explanation: 'Moderate match - has industrial metal frame but lacks the complete office context.',
        metadata: { collected_at: new Date().toISOString() }
      },
      {
        _id: '6',
        image_url: 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400',
        pin_url: 'https://pinterest.com/pin/6',
        title: 'Colorful Art Studio',
        description: 'Creative workspace with bright colors and art supplies',
        match_score: 0.34,
        status: 'disqualified',
        ai_explanation: 'Poor match - too colorful and artistic, lacks industrial aesthetic and office functionality.',
        metadata: { collected_at: new Date().toISOString() }
      }
    ];

    setTimeout(() => {
      setPins(mockPins);
      setLoading(false);
    }, 1000);
  }, [promptId]);

  useEffect(() => {
    let filtered = pins;

    if (statusFilter !== 'all') {
      filtered = filtered.filter(pin => pin.status === statusFilter);
    }

    filtered = filtered.filter(pin => pin.match_score >= scoreThreshold);

    setFilteredPins(filtered);
  }, [pins, statusFilter, scoreThreshold]);

  const approvedCount = pins.filter(pin => pin.status === 'approved').length;
  const disqualifiedCount = pins.filter(pin => pin.status === 'disqualified').length;
  const avgScore = pins.length > 0 ? pins.reduce((sum, pin) => sum + pin.match_score, 0) / pins.length : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 dark:bg-gradient-to-br dark:from-gray-900 dark:via-blue-900 dark:to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4 text-emerald-600 dark:text-emerald-400" />
          <p className="text-gray-600 dark:text-gray-300">Loading validated results...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:bg-gradient-to-br dark:from-gray-900 dark:via-blue-900 dark:to-indigo-900 p-4 relative">
      <ThemeToggle />
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <button 
              onClick={onBack}
              className="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white transition-colors mb-4"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Search
            </button>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Validation Results</h1>
            <p className="text-gray-600 dark:text-gray-300">
              AI-validated Pinterest images for: <span className="font-medium text-blue-600 dark:text-blue-400">"{originalPrompt}"</span>
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}`}
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}`}
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white/80 dark:bg-gray-800/90 backdrop-blur-sm rounded-xl p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Approved</span>
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{approvedCount}</div>
          </div>
          <div className="bg-white/80 dark:bg-gray-800/90 backdrop-blur-sm rounded-xl p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Disqualified</span>
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{disqualifiedCount}</div>
          </div>
          <div className="bg-white/80 dark:bg-gray-800/90 backdrop-blur-sm rounded-xl p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <Star className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Avg Score</span>
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{Math.round(avgScore * 100)}%</div>
          </div>
          <div className="bg-white/80 dark:bg-gray-800/90 backdrop-blur-sm rounded-xl p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Total</span>
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{pins.length}</div>
          </div>
        </div>

        <div className="bg-white/80 dark:bg-gray-800/90 backdrop-blur-sm rounded-xl p-6 border border-gray-200 dark:border-gray-700 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-5 h-5 text-gray-600 dark:text-gray-300" />
            <span className="font-medium text-gray-700 dark:text-gray-200">Filters</span>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-600 dark:text-gray-300">Status:</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="px-3 py-1 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="all">All</option>
                <option value="approved">Approved</option>
                <option value="disqualified">Disqualified</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-600 dark:text-gray-300">Min Score:</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={scoreThreshold}
                onChange={(e) => setScoreThreshold(parseFloat(e.target.value))}
                className="w-24"
              />
              <span className="text-sm text-gray-600 dark:text-gray-300 w-12">{(scoreThreshold * 100).toFixed(0)}%</span>
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Showing {filteredPins.length} of {pins.length} results
            </div>
          </div>
        </div>

        <div className={viewMode === 'grid' 
          ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' 
          : 'space-y-4'
        }>
          {filteredPins.map((pin) => (
            <div key={pin._id} className={`bg-white/80 dark:bg-gray-800/90 backdrop-blur-sm rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-all duration-200 ${
              viewMode === 'list' ? 'flex gap-4 p-4' : ''
            }`}>
              <div className={viewMode === 'list' ? 'w-32 h-32 flex-shrink-0' : 'aspect-square'}>
                <img
                  src={pin.image_url}
                  alt={pin.title}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className={viewMode === 'list' ? 'flex-1' : 'p-4'}>
                <div className="flex items-center justify-between mb-2">
                  <StatusBadge status={pin.status} />
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4 text-yellow-500" />
                    <span className="text-sm font-medium">{(pin.match_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1 line-clamp-2">{pin.title}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-2">{pin.description}</p>
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 mb-3">
                  <p className="text-xs text-gray-700 dark:text-gray-300">{pin.ai_explanation}</p>
                </div>
                <div className="flex items-center justify-between">
                  <ScoreBar score={pin.match_score} className="flex-1" />
                  <a
                    href={pin.pin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-3 p-2 text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredPins.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 dark:text-gray-500 mb-4">
              <Filter className="w-12 h-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No results found</h3>
            <p className="text-gray-600 dark:text-gray-300">Try adjusting your filters to see more results.</p>
          </div>
        )}
      </div>
    </div>
  );
}
