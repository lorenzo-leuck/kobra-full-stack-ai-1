import { useState, useEffect } from 'react';
import PromptSubmission from './components/PromptSubmission';
import AgentProgress from './components/AgentProgress';
import ImageReview from './components/ImageReview';
import ErrorBoundary from './components/ErrorBoundary';
import { ApiService } from './services/api';
import type { AppState } from './types';

function App() {
  const [currentState, setCurrentState] = useState<AppState>('prompt');
  const [currentPrompt, setCurrentPrompt] = useState('');
  const [promptId, setPromptId] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Initialize theme on app load
    const theme = localStorage.getItem('theme') || 'light';
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    }
  }, []);

  const handlePromptSubmit = async (prompt: string) => {
    setCurrentPrompt(prompt);
    setIsLoading(true);
    
    try {
      // Call real API service
      const response = await ApiService.submitPrompt(prompt);
      setPromptId(response.prompt_id);
      setCurrentState('progress');
    } catch (error) {
      console.error('Failed to submit prompt:', error);
      // TODO: Add proper error handling/display
      alert('Failed to submit prompt. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleProgressComplete = () => {
    setCurrentState('review');
  };

  const handleBackToPrompt = () => {
    setCurrentState('prompt');
    setCurrentPrompt('');
    setPromptId('');
  };

  const handleHistorySelect = async (selectedPromptId: string) => {
    try {
      // Fetch the prompt details to get the original text
      const response = await ApiService.getPromptStatus(selectedPromptId);
      setCurrentPrompt(response.prompt?.text || '');
      setPromptId(selectedPromptId);
      setCurrentState('review');
    } catch (error) {
      console.error('Failed to load prompt history:', error);
      alert('Failed to load prompt. Please try again.');
    }
  };

  return (
    <ErrorBoundary>
      <div className="App min-h-screen">
        {currentState === 'prompt' && (
          <PromptSubmission 
            onSubmit={handlePromptSubmit} 
            isLoading={isLoading}
            onHistorySelect={handleHistorySelect}
          />
        )}
        
        {currentState === 'progress' && (
          <AgentProgress 
            promptId={promptId}
            onComplete={handleProgressComplete}
          />
        )}
        
        {currentState === 'review' && (
          <ImageReview 
            promptId={promptId}
            originalPrompt={currentPrompt}
            onBack={handleBackToPrompt}
          />
        )}
      </div>
    </ErrorBoundary>
  );
}

export default App;
