import { useEffect, useState } from 'react';
import { CheckCircle, Clock, AlertCircle, Loader2, Heart, Search, Brain } from 'lucide-react';
import ThemeToggle from './ThemeToggle';

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
      status: 'active',
      progress: 0,
      logs: ['Initializing Pinterest session...', 'Logging into account...']
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

  useEffect(() => {
    // TODO: Replace with actual API polling
    // const pollStatus = async () => {
    //   try {
    //     const response = await fetch(`/api/prompts/${promptId}/status`);
    //     const data = await response.json();
    //     updateStagesFromAPI(data);
    //   } catch (error) {
    //     console.error('Failed to poll status:', error);
    //   }
    // };

    // Simulate progress for demo
    const simulateProgress = () => {
      let currentStage = 0;
      let progress = 0;

      const interval = setInterval(() => {
        progress += Math.random() * 15;
        
        setStages(prev => prev.map((stage, index) => {
          if (index < currentStage) {
            return { ...stage, status: 'completed' as const, progress: 100 };
          } else if (index === currentStage) {
            const stageProgress = Math.min(progress, 100);
            const newLogs = [...(stage.logs || [])];
            
            if (stage.id === 'warmup' && stageProgress > 20 && newLogs.length < 4) {
              newLogs.push(...['Searching for relevant pins...', 'Saving pins to board...', 'Interacting with content...']);
            } else if (stage.id === 'scraping' && stageProgress > 30 && newLogs.length < 3) {
              newLogs.push('Scraping feed images...', `Collected ${Math.floor(stageProgress/5)} of 25 pins...`);
            } else if (stage.id === 'validation' && stageProgress > 40 && newLogs.length < 3) {
              newLogs.push('Loading AI model...', `Validating pin ${Math.floor(stageProgress/10)} of 25...`);
            }

            return {
              ...stage,
              status: stageProgress >= 100 ? 'completed' as const : 'active' as const,
              progress: stageProgress,
              logs: newLogs
            };
          } else {
            return { ...stage, status: 'pending' as const };
          }
        }));

        if (progress >= 100) {
          currentStage++;
          progress = 0;
          
          if (currentStage >= 3) {
            clearInterval(interval);
            setOverallProgress(100);
            setTimeout(() => onComplete(), 1000);
          }
        }

        const completedStages = Math.min(currentStage, 3);
        const currentStageProgress = Math.min(progress, 100);
        setOverallProgress((completedStages * 100 + currentStageProgress) / 3);
      }, 800);

      return () => clearInterval(interval);
    };

    const cleanup = simulateProgress();
    return cleanup;
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
            <span className="text-sm font-medium text-gray-600 dark:text-gray-300">{Math.round(overallProgress)}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-4">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${overallProgress}%` }}
            />
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
