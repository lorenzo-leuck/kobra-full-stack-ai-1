import { useState } from 'react';
import PromptSubmission from './components/PromptSubmission';
import AgentProgress from './components/AgentProgress';
import ImageReview from './components/ImageReview';
import ErrorBoundary from './components/ErrorBoundary';
import type { AppState } from './types';

function App() {
  const [currentState, setCurrentState] = useState<AppState>('prompt');
  const [currentPrompt, setCurrentPrompt] = useState('');
  const [promptId, setPromptId] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handlePromptSubmit = async (prompt: string) => {
    setCurrentPrompt(prompt);
    setIsLoading(true);
    
    // Simulate API response
    const mockPromptId = `prompt_${Date.now()}`;
    setPromptId(mockPromptId);
    
    setCurrentState('progress');
    setIsLoading(false);
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
