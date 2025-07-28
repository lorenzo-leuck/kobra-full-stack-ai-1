import { useState } from 'react';
import { Search, Sparkles, ArrowRight } from 'lucide-react';
import ThemeToggle from './ThemeToggle';

interface PromptSubmissionProps {
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
}

export default function PromptSubmission({ onSubmit, isLoading }: PromptSubmissionProps) {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !isLoading) {
      onSubmit(prompt.trim());
    }
  };

  const examplePrompts = [
    "boho minimalist bedroom",
    "cozy industrial home office", 
    "cottagecore kitchen",
    "modern scandinavian living room",
    "vintage art deco bathroom"
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 dark:bg-gradient-to-br dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4 relative">
      <ThemeToggle />
      <div className="max-w-2xl w-full">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 p-4 rounded-full">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Pinterest AI Curator
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-lg mx-auto">
            Enhance your feed with ai-driven visual discovery
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mb-8">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe your visual style... (e.g., 'cozy industrial home office')"
              className="w-full pl-12 pr-40 py-4 text-lg border-2 border-gray-200 dark:border-gray-700 rounded-2xl focus:border-purple-500 dark:focus:border-purple-400 focus:ring-4 focus:ring-purple-100 dark:focus:ring-purple-500/30 outline-none transition-all duration-200 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!prompt.trim() || isLoading}
              className="absolute right-2 top-2 bottom-2 px-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2 font-medium text-sm"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  Start Agent
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>

        <div className="bg-white/60 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            Try these examples
          </h3>
          <div className="flex flex-wrap gap-2">
            {examplePrompts.map((example, index) => (
              <button
                key={index}
                onClick={() => setPrompt(example)}
                disabled={isLoading}
                className="px-4 py-2 bg-white dark:bg-gray-700/80 border border-gray-200 dark:border-gray-600 rounded-full text-sm text-gray-700 dark:text-gray-200 hover:bg-purple-50 dark:hover:bg-gray-600 hover:border-purple-200 dark:hover:border-gray-500 hover:text-purple-700 dark:hover:text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
