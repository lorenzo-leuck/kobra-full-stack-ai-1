import { useEffect, useState } from 'react';
import { CheckCircle, Clock, AlertCircle, Loader2, Heart, Search, Brain } from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import { websocketService } from '../services/websocket';
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
      description: 'Engaging with Pinterest to align recommendations',
      icon: <Heart className="w-5 h-5" />,
      status: 'pending',
      progress: 0,
      logs: []
    },
    {
      id: 'scraping',
      name: 'Image Collection',
      description: 'Scraping top image results from Pinterest',
      icon: <Search className="w-5 h-5" />,
      status: 'pending',
      progress: 0,
      logs: []
    },
    {
      id: 'validation',
      name: 'AI Validation',
      description: 'Validating images with AI model',
      icon: <Brain className="w-5 h-5" />,
      status: 'pending',
      progress: 0,
      logs: []
    }
  ]);

  const [overallProgress, setOverallProgress] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('connecting');
  const [currentStatus, setCurrentStatus] = useState('Initializing workflow...');
  const [isCompleted, setIsCompleted] = useState(false);

  useEffect(() => {
    let mounted = true;

    const connectWebSocket = async () => {
      try {
        setConnectionStatus('connecting');
        await websocketService.connect(promptId);
        
        if (mounted) {
          setConnectionStatus('connected');
        }
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        if (mounted) {
          setConnectionStatus('error');
        }
      }
    };

    const handleWebSocketMessage = (message: any) => {
      if (!mounted) return;

      if (message.type === 'status_update') {
        const { overall_status, progress, messages, current_step, total_steps } = message.data;
        
        setOverallProgress(progress);
        setCurrentStatus(messages[messages.length - 1] || 'Processing...');
        
        if (overall_status === 'completed') {
          setIsCompleted(true);
          setTimeout(() => {
            if (mounted) onComplete();
          }, 1500);
        }

        // Update stages based on current step
        setStages(prev => prev.map((stage, index) => {
          if (index < current_step - 1) {
            return { ...stage, status: 'completed' as const, progress: 100 };
          } else if (index === current_step - 1) {
            return { ...stage, status: 'active' as const, progress: (progress / total_steps) * 100 };
          } else {
            return { ...stage, status: 'pending' as const, progress: 0 };
          }
        }));
      }

      if (message.type === 'session_update') {
        const { stage, logs } = message.data;
        
        setStages(prev => prev.map(s => {
          if (s.id === stage) {
            return { ...s, logs: logs || [] };
          }
          return s;
        }));
      }
    };

    // Initial status fetch
    const fetchInitialStatus = async () => {
      try {
        const statusData = await ApiService.getPromptStatus(promptId);
        setOverallProgress(statusData.overall_progress);
        setCurrentStatus(`Current stage: ${statusData.current_stage}`);
        
        // Update stages based on sessions
        if (statusData.sessions) {
          setStages(prev => prev.map(stage => {
            const session = statusData.sessions.find(s => s.stage === stage.id);
            if (session) {
              return {
                ...stage,
                status: session.status === 'completed' ? 'completed' : 
                       session.status === 'running' ? 'active' : 'pending',
                logs: session.logs || []
              };
            }
            return stage;
          }));
        }
      } catch (error) {
        console.error('Failed to fetch initial status:', error);
      }
    };

    websocketService.addListener(handleWebSocketMessage);
    connectWebSocket();
    fetchInitialStatus();

    return () => {
      mounted = false;
      websocketService.removeListener(handleWebSocketMessage);
      websocketService.disconnect();
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
                connectionStatus === 'connected' ? 'bg-green-500' :
                connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                connectionStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'
              }`} />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">{Math.round(overallProgress)}%</span>
            </div>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-4">
            <div 
              className={`h-3 rounded-full transition-all duration-500 ease-out ${
                isCompleted ? 'bg-gradient-to-r from-green-500 to-emerald-600' :
                'bg-gradient-to-r from-blue-500 to-purple-600'
              }`}
              style={{ width: `${overallProgress}%` }}
            />
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {currentStatus}
          </div>
        </div>

        <div className="space-y-6">
          {stages.map((stage) => (
            <div key={stage.id} className="bg-white/80 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-full ${
                      stage.status === 'completed' ? 'bg-green-100 dark:bg-green-900/30' :
                      stage.status === 'active' ? 'bg-blue-100 dark:bg-blue-900/30' :
                      stage.status === 'failed' ? 'bg-red-100 dark:bg-red-900/30' : 'bg-gray-100 dark:bg-gray-700'
                    }`}>
                      {stage.status === 'pending' ? stage.icon : getStatusIcon(stage.status)}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-800 dark:text-white">{stage.name}</h3>
                      <p className="text-gray-600 dark:text-gray-300">{stage.description}</p>
                    </div>
                  </div>

                </div>



                {stage.logs && stage.logs.length > 0 && (
                  <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 mt-4">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Activity Log</h4>
                    <div className="space-y-1">
                      {stage.logs.map((log, logIndex) => (
                        <div key={logIndex} className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                          <div className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full flex-shrink-0" />
                          {log}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
