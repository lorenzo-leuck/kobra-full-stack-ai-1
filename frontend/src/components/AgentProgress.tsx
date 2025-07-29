import { useEffect, useState } from 'react';
import { CheckCircle, Clock, AlertCircle, Loader2, Heart, Search, Brain } from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import { pollingService } from '../services/polling';
import { ApiService } from '../services/api';

interface AgentProgressProps {
  promptId: string;
  onComplete: () => void;
}

interface ProgressStage {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  status: 'pending' | 'active' | 'completed' | 'failed';
  progress?: number;
  logs?: string[];
}

export default function AgentProgress({ promptId, onComplete }: AgentProgressProps) {
  const [stages, setStages] = useState<ProgressStage[]>([
    {
      id: 'warmup',
      name: 'Pinterest Warm-up',
      description: '',
      icon: <Heart className="w-5 h-5" />,
      status: 'pending',
      progress: 0,
      logs: []
    },
    {
      id: 'scraping',
      name: 'Image Collection',
      description: '',
      icon: <Search className="w-5 h-5" />,
      status: 'pending',
      progress: 0,
      logs: []
    },
    {
      id: 'validation',
      name: 'AI Validation',
      description: '',
      icon: <Brain className="w-5 h-5" />,
      status: 'pending',
      progress: 0,
      logs: []
    }
  ]);

  const [overallProgress, setOverallProgress] = useState(0);
  const [pollingStatus, setPollingStatus] = useState<'starting' | 'active' | 'stopped' | 'error'>('starting');
  const [currentStatus, setCurrentStatus] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);

  useEffect(() => {
    let mounted = true;

    const handlePollingMessage = (message: any) => {
      if (!mounted) return;

      console.log('🎯 Processing polling message:', message.type, message.data);

      if (message.type === 'status_update') {
        const { overall_status, progress, messages } = message.data;
        
        console.log('📊 Status update:', { overall_status, progress, messages });
        
        setOverallProgress(progress);
        setCurrentStatus(messages[messages.length - 1] || 'Processing...');
        
        if (overall_status === 'completed') {
          console.log('🎉 Workflow completed!');
          setIsCompleted(true);
          // If progress is 100%, transition immediately, otherwise show completion animation
          const delay = progress >= 100 ? 500 : 1500;
          setTimeout(() => {
            if (mounted) onComplete();
          }, delay);
        }
      }

      if (message.type === 'session_update') {
        const { stage, status, logs } = message.data;
        
        console.log('📝 Session update:', { stage, status, logs });
        
        setStages(prev => prev.map(s => {
          if (s.id === stage) {
            // Map backend status to frontend status
            let frontendStatus: 'pending' | 'active' | 'completed' | 'failed';
            switch (status) {
              case 'running':
                frontendStatus = 'active';
                break;
              case 'completed':
                frontendStatus = 'completed';
                break;
              case 'failed':
                frontendStatus = 'failed';
                break;
              default:
                frontendStatus = 'pending';
            }
            
            return { 
              ...s, 
              status: frontendStatus,
              logs: logs || [] 
            };
          }
          return s;
        }));
      }
    };

    // Initial status fetch
    const fetchInitialStatus = async () => {
      try {
        console.log('📊 Fetching initial status for prompt:', promptId);
        const statusData = await ApiService.getPromptStatus(promptId);
        setOverallProgress(statusData.overall_progress || 0);
        
        // Update stages based on sessions
        if (statusData.sessions) {
          setStages(prev => prev.map(stage => {
            const session = statusData.sessions.find(s => s.stage === stage.id);
            if (session) {
              return {
                ...stage,
                status: session.status === 'completed' ? 'completed' : 
                       session.status === 'running' ? 'active' : 
                       session.status === 'failed' ? 'failed' : 'pending',
                logs: session.logs || []
              };
            }
            return stage;
          }));
        }
      } catch (error) {
        console.error('Failed to fetch initial status:', error);
        setPollingStatus('error');
      }
    };

    // Start polling
    console.log('🔄 Starting polling for prompt:', promptId);
    setPollingStatus('starting');
    
    pollingService.addListener(handlePollingMessage);
    pollingService.start(promptId);
    setPollingStatus('active');

    // Fetch initial status
    fetchInitialStatus();

    return () => {
      console.log('🧹 Cleaning up polling service');
      mounted = false;
      pollingService.removeListener(handlePollingMessage);
      pollingService.stop();
      setPollingStatus('stopped');
    };
  }, [promptId, onComplete]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'active':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:bg-gradient-to-br dark:from-gray-900 dark:via-blue-900 dark:to-indigo-900 p-4 relative">
      <ThemeToggle />
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">AI Agent Working</h1>
          <p className="text-gray-600 dark:text-gray-300">Processing your visual prompt with intelligent automation</p>
        </div>

        <div className="bg-white/80 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl p-8 border border-gray-200 dark:border-gray-700 mb-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Overall Progress</h2>
            <div className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full ${
                pollingStatus === 'active' ? 'bg-green-500' :
                pollingStatus === 'starting' ? 'bg-yellow-500 animate-pulse' :
                pollingStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'
              }`} />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">{Math.round(overallProgress)}%</span>
            </div>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-4 relative overflow-hidden">
            <div 
              className={`h-3 rounded-full transition-all duration-500 ease-out ${
                isCompleted ? 'bg-gradient-to-r from-green-500 to-emerald-600' :
                'bg-gradient-to-r from-blue-500 to-purple-600'
              }`}
              style={{ width: `${overallProgress}%` }}
            />
            {/* Loading shimmer animation when progress is 0% or very low */}
            {overallProgress <= 5 && !isCompleted && (
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse">
                <div className="h-full w-full bg-gradient-to-r from-blue-400/30 via-purple-400/30 to-blue-400/30 animate-shimmer" />
              </div>
            )}
          </div>
          {currentStatus && currentStatus !== 'pending' && (
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {currentStatus}
            </div>
          )}
        </div>

        <div className="space-y-6">
          {stages.map((stage) => {
            const isCompleted = stage.status === 'completed';
            const isActive = stage.status === 'active';
            const isPending = stage.status === 'pending';
            const isFailed = stage.status === 'failed';
            
            return (
              <div 
                key={stage.id} 
                className={`bg-white/80 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl border-2 transition-all duration-300 overflow-hidden ${
                  isCompleted ? 'border-green-500 shadow-green-200/50 dark:shadow-green-900/30 shadow-lg' :
                  isActive ? 'border-blue-500 shadow-blue-200/50 dark:shadow-blue-900/30 shadow-lg animate-pulse' :
                  isFailed ? 'border-red-500 shadow-red-200/50 dark:shadow-red-900/30 shadow-lg' :
                  isPending ? 'border-yellow-500 shadow-yellow-200/50 dark:shadow-yellow-900/30 shadow-lg' :
                  'border-gray-200 dark:border-gray-700'
                }`}
              >
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <div className={`p-3 rounded-full transition-all duration-300 ${
                        isCompleted ? 'bg-green-100 dark:bg-green-900/30' :
                        isActive ? 'bg-blue-100 dark:bg-blue-900/30' :
                        isFailed ? 'bg-red-100 dark:bg-red-900/30' :
                        isPending ? 'bg-yellow-100 dark:bg-yellow-900/30' :
                        'bg-gray-100 dark:bg-gray-700'
                      }`}>
                        {isActive ? (
                          <div className="relative">
                            {stage.icon}
                            <div className="absolute inset-0 flex items-center justify-center">
                              <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
                            </div>
                          </div>
                        ) : isPending ? (
                          stage.icon
                        ) : (
                          getStatusIcon(stage.status)
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-lg font-semibold text-gray-800 dark:text-white">{stage.name}</h3>
                          {isActive && (
                            <div className="flex items-center gap-1">
                              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                              <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">ACTIVE</span>
                            </div>
                          )}
                          {isCompleted && (
                            <div className="flex items-center gap-1">
                              <div className="w-2 h-2 bg-green-500 rounded-full" />
                              <span className="text-xs text-green-600 dark:text-green-400 font-medium">COMPLETED</span>
                            </div>
                          )}
                        </div>
                        <p className="text-gray-600 dark:text-gray-300">{stage.description}</p>
                      </div>
                    </div>
                    
                    {/* Status indicator - only show for active, completed, or failed */}
                    {(isActive || isCompleted || isFailed) && (
                      <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                        isCompleted ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' :
                        isActive ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' :
                        'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                      }`}>
                        {stage.status.toUpperCase()}
                      </div>
                    )}
                  </div>

                  {/* Progress bar for active stage */}
                  {isActive && (
                    <div className="mb-4">
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div className="h-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full animate-pulse" style={{ width: '60%' }} />
                      </div>
                    </div>
                  )}

                  {/* Activity logs */}
                  {stage.logs && stage.logs.length > 0 && (
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 mt-4">
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                        Activity Log
                      </h4>
                      <div className="space-y-2 max-h-32 overflow-y-auto">
                        {stage.logs.map((log, logIndex) => (
                          <div key={logIndex} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full flex-shrink-0 mt-1.5" />
                            <span className="leading-relaxed">{log}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  

                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
