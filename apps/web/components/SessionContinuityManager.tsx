/**
 * 会话连续性管理组件
 * 静默恢复对话历史，显示简洁的状态提示
 */
import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface SessionContinuityManagerProps {
  projectId: string;
  onSessionRestore?: (sessionInfo: SessionInfo) => void;
  onConversationLoaded?: (hasConversation: boolean) => void;
}

interface SessionInfo {
  hasActiveConversation: boolean;
  providers: string[];
  lastActivity: string;
  messageCount: number;
}

interface ConversationState {
  [provider: string]: {
    active: boolean;
    summary: {
      total_messages: number;
      user_messages: number;
      assistant_messages: number;
      has_system_prompt: boolean;
    };
  };
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080';

export default function SessionContinuityManager({ 
  projectId, 
  onSessionRestore,
  onConversationLoaded
}: SessionContinuityManagerProps) {
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showStatus, setShowStatus] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  useEffect(() => {
    checkAndRestoreConversations();
  }, [projectId]);

  const checkAndRestoreConversations = async () => {
    try {
      setIsLoading(true);
      
      const response = await fetch(`${API_BASE}/api/conversation/${projectId}/providers`);
      if (response.ok) {
        const data: ConversationState = await response.json();
        
        // 检查是否有活跃的对话
        const activeProviders = Object.entries(data)
          .filter(([_, info]) => info.active && info.summary.total_messages > 0)
          .map(([provider, _]) => provider);
        
        if (activeProviders.length > 0) {
          const totalMessages = Object.values(data)
            .filter(info => info.active)
            .reduce((sum, info) => sum + info.summary.total_messages, 0);
          
          const sessionInfo: SessionInfo = {
            hasActiveConversation: true,
            providers: activeProviders,
            lastActivity: new Date().toISOString(),
            messageCount: totalMessages
          };
          
          setSessionInfo(sessionInfo);
          
          // 静默恢复对话
          if (onSessionRestore) {
            onSessionRestore(sessionInfo);
          }
          
          // 显示简洁的恢复提示
          const providerNames = activeProviders.map(formatProviderName).join('、');
          setStatusMessage(`已恢复与 ${providerNames} 的对话历史 (${totalMessages}条消息)`);
          setShowStatus(true);
          
          // 3秒后自动隐藏提示
          setTimeout(() => setShowStatus(false), 3000);
          
          if (onConversationLoaded) {
            onConversationLoaded(true);
          }
        } else {
          if (onConversationLoaded) {
            onConversationLoaded(false);
          }
        }
      }
    } catch (error) {
      console.error('Failed to check existing conversations:', error);
      if (onConversationLoaded) {
        onConversationLoaded(false);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const formatProviderName = (provider: string) => {
    const providerNames: { [key: string]: string } = {
      deepseek: 'DeepSeek',
      qwen: '通义千问',
      kimi: 'Kimi',
      doubao: '豆包'
    };
    return providerNames[provider] || provider;
  };

  // 加载状态显示
  if (isLoading) {
    return (
      <div className="absolute top-4 right-4 z-50">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 px-3 py-2 flex items-center gap-2"
        >
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm text-gray-600 dark:text-gray-400">检查对话历史...</span>
        </motion.div>
      </div>
    );
  }

  // 恢复状态提示
  return (
    <AnimatePresence>
      {showStatus && sessionInfo && (
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95 }}
          className="absolute top-4 right-4 z-50 max-w-sm"
        >
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3 shadow-lg">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-0.5">
                <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-green-800 dark:text-green-200 mb-1">
                  对话已恢复
                </p>
                <p className="text-xs text-green-700 dark:text-green-300">
                  {statusMessage}
                </p>
              </div>
              <button
                onClick={() => setShowStatus(false)}
                className="flex-shrink-0 text-green-400 hover:text-green-600 dark:text-green-500 dark:hover:text-green-300"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}