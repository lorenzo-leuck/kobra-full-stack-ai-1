import { useState, useEffect } from 'react';
import { X, Clock, CheckCircle, XCircle, AlertCircle, Loader } from 'lucide-react';
import { ApiService } from '../services/api';
import type { Prompt } from '../types';

interface HistorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onPromptSelect: (promptId: string) => void;
}

export default function HistorySidebar({ isOpen, onClose, onPromptSelect }: HistorySidebarProps) {
  const [promptHistory, setPromptHistory] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadHistory();
    }
  }, [isOpen]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const response = await ApiService.getPromptHistory(20);
      setPromptHistory(response.prompts);
    } catch (error) {
      console.error('Failed to load prompt history:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'pending':
        return <Loader className="w-4 h-4 text-yellow-500 animate-spin" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 dark:text-green-400';
      case 'error': return 'text-red-600 dark:text-red-400';
      case 'pending': return 'text-yellow-600 dark:text-yellow-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const handlePromptClick = (prompt: Prompt) => {
    if (prompt.status === 'completed') {
      onPromptSelect(prompt._id);
      onClose();
    }
  };

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 transition-opacity duration-300"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div className={`fixed top-0 left-0 h-full w-80 bg-white dark:bg-gray-900 shadow-xl z-50 transform transition-transform duration-300 ease-in-out ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Prompt History
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-center">
                <Loader className="w-8 h-8 text-purple-600 animate-spin mx-auto mb-2" />
                <p className="text-gray-500 dark:text-gray-400">Loading history...</p>
              </div>
            </div>
          ) : promptHistory.length === 0 ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-center">
                <Clock className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">No prompt history yet</p>
                <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                  Your previous prompts will appear here
                </p>
              </div>
            </div>
          ) : (
            <div className="p-2">
              {promptHistory.map((prompt) => (
                <button
                  key={prompt._id}
                  onClick={() => handlePromptClick(prompt)}
                  disabled={prompt.status !== 'completed'}
                  className={`w-full p-4 mb-2 text-left rounded-lg border transition-all duration-200 ${
                    prompt.status === 'completed'
                      ? 'hover:bg-purple-50 dark:hover:bg-purple-900/20 hover:border-purple-200 dark:hover:border-purple-700 cursor-pointer'
                      : 'cursor-not-allowed opacity-60'
                  } bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700`}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-1">
                      {getStatusIcon(prompt.status)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 dark:text-white text-sm leading-relaxed">
                        {prompt.text}
                      </p>
                      <div className="flex items-center gap-3 mt-2">
                        <span className={`text-xs font-medium capitalize ${getStatusColor(prompt.status)}`}>
                          {prompt.status}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {formatDate(prompt.created_at)}
                        </span>
                      </div>
                      {prompt.status === 'completed' && (
                        <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                          Click to view results →
                        </p>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
