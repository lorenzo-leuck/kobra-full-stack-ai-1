import { ApiService } from './api';
import type { Session } from '../types';

interface StatusUpdate {
  type: 'status_update';
  data: {
    prompt_id: string;
    overall_status: string;
    current_step: number;
    total_steps: number;
    progress: number;
    messages: string[];
  };
}

interface SessionUpdate {
  type: 'session_update';
  data: {
    prompt_id: string;
    session_id: string;
    stage: string;
    status: string;
    logs: string[];
  };
}

type PollingMessage = StatusUpdate | SessionUpdate;

export class PollingService {
  private intervalId: number | null = null;
  private promptId: string | null = null;
  private listeners: Set<(message: PollingMessage) => void> = new Set();
  private isPolling = false;
  private pollInterval = 2000; // Poll every 2 seconds
  private lastStatus: any = null;
  private lastSessions: Session[] = [];

  start(promptId: string): void {
    this.promptId = promptId;
    this.isPolling = true;
    this.lastStatus = null;
    this.lastSessions = [];
    
    console.log('🔄 Starting polling for prompt:', promptId);
    
    // Start polling immediately
    this.poll();
    
    // Set up interval for continuous polling
    this.intervalId = window.setInterval(() => {
      if (this.isPolling) {
        this.poll();
      }
    }, this.pollInterval);
  }

  private async poll(): Promise<void> {
    if (!this.promptId || !this.isPolling) return;

    try {
      console.log('📊 Polling status for prompt:', this.promptId);
      
      const statusResponse = await ApiService.getPromptStatus(this.promptId);
      const { prompt, sessions, overall_progress, current_stage } = statusResponse;

      // Check if overall status changed
      if (!this.lastStatus || 
          this.lastStatus.status !== prompt.status ||
          this.lastStatus.overall_progress !== overall_progress) {
        
        console.log('Status update:', {
          status: prompt.status,
          progress: overall_progress,
          stage: current_stage
        });

        // Use backend progress percentage as primary source
        let progressPercentage = overall_progress;
        
        // If backend doesn't provide progress, calculate from sessions
        if (progressPercentage === undefined || progressPercentage === null) {
          if (sessions && sessions.length > 0) {
            const completedSessions = sessions.filter(s => s.status === 'completed').length;
            const totalSessions = 3; // warmup, scraping, validation
            progressPercentage = (completedSessions / totalSessions) * 100;
          } else {
            progressPercentage = 0;
          }
        }
        
        // If workflow is completed, ensure 100%
        if (prompt.status === 'completed') {
          progressPercentage = 100;
        }
        
        console.log('🔄 Final progress calculation:', {
          backend_progress: overall_progress,
          calculated_progress: progressPercentage,
          workflow_status: prompt.status
        });

        // Create status update message
        const statusUpdate: StatusUpdate = {
          type: 'status_update',
          data: {
            prompt_id: this.promptId,
            overall_status: prompt.status,
            current_step: sessions ? sessions.filter(s => s.status === 'completed').length : 0,
            total_steps: 3, // warmup, scraping, validation
            progress: progressPercentage,
            messages: [current_stage || 'Processing...']
          }
        };

        this.notifyListeners(statusUpdate);
        this.lastStatus = { status: prompt.status, overall_progress: progressPercentage };
      }

      // Check for session updates
      sessions.forEach((session, index) => {
        const lastSession = this.lastSessions[index];
        
        // If session is new or status/logs changed
        if (!lastSession || 
            lastSession.status !== session.status ||
            JSON.stringify(lastSession.logs) !== JSON.stringify(session.logs)) {
          
          console.log('📝 Session update detected:', {
            stage: session.stage,
            status: session.status,
            logs: session.logs?.length || 0
          });

          const sessionUpdate: SessionUpdate = {
            type: 'session_update',
            data: {
              prompt_id: this.promptId!,
              session_id: session._id,
              stage: session.stage,
              status: session.status,
              logs: session.logs || []
            }
          };

          this.notifyListeners(sessionUpdate);
        }
      });

      this.lastSessions = [...sessions];

      // Stop polling if workflow is completed or failed
      if (prompt.status === 'completed' || prompt.status === 'error') {
        console.log('✅ Workflow finished, stopping polling');
        this.stop();
      }

    } catch (error) {
      console.error('❌ Polling error:', error);
      // Continue polling even on errors, but with exponential backoff
      this.pollInterval = Math.min(this.pollInterval * 1.2, 10000);
    }
  }

  addListener(callback: (message: PollingMessage) => void): void {
    this.listeners.add(callback);
  }

  removeListener(callback: (message: PollingMessage) => void): void {
    this.listeners.delete(callback);
  }

  private notifyListeners(message: PollingMessage): void {
    this.listeners.forEach(callback => {
      try {
        callback(message);
      } catch (error) {
        console.error('Error in polling listener:', error);
      }
    });
  }

  stop(): void {
    console.log('🛑 Stopping polling service');
    this.isPolling = false;
    
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    
    this.promptId = null;
    this.listeners.clear();
    this.lastStatus = null;
    this.lastSessions = [];
    this.pollInterval = 2000; // Reset poll interval
  }

  isActive(): boolean {
    return this.isPolling && this.intervalId !== null;
  }
}

export const pollingService = new PollingService();
