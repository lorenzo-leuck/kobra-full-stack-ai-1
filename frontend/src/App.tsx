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

  return (
    <ErrorBoundary>
      <div className="App min-h-screen">
        {currentState === 'prompt' && (
          <PromptSubmission 
            onSubmit={handlePromptSubmit} 
            isLoading={isLoading}
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
