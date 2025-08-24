/**
 * 对话状态指示器
 * 在聊天界面中显示当前对话的简洁状态信息
 */
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ConversationStatusIndicatorProps {
  projectId: string;
  activeProvider?: string;
  className?: string;
}

interface ConversationSummary {
  total_messages: number;
  user_messages: number;
  assistant_messages: number;
  provider: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080';

export default function ConversationStatusIndicator({
  projectId,
  activeProvider,
  className = ""
}: ConversationStatusIndicatorProps) {
  const [summary, setSummary] = useState<ConversationSummary | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (activeProvider) {
      loadConversationSummary();
    }
  }, [projectId, activeProvider]);

  const loadConversationSummary = async () => {
    if (!activeProvider) return;
    
    try {
      const response = await fetch(
        `${API_BASE}/api/conversation/${projectId}/summary?provider=${activeProvider}`
      );
      if (response.ok) {
        const data = await response.json();
        setSummary(data);
        setIsVisible(data.total_messages > 0);
      }
    } catch (error) {
      console.error('Failed to load conversation summary:', error);
    }
  };

  const getProviderDisplayName = (provider: string) => {
    const names: { [key: string]: string } = {
      deepseek: 'DeepSeek',
      qwen: '通义千问',
      kimi: 'Kimi',
      doubao: '豆包'
    };
    return names[provider] || provider;
  };

  const getProviderIcon = (provider: string) => {
    const icons: { [key: string]: string } = {
      deepseek: '🔍',
      qwen: '🐉',
      kimi: '🌙',
      doubao: '🫘'
    };
    return icons[provider] || '🤖';
  };

  if (!isVisible || !summary || summary.total_messages === 0) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className={`inline-flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-full text-xs ${className}`}
      >
        <span className="text-sm">
          {getProviderIcon(summary.provider)}
        </span>
        
        <div className="flex items-center gap-1.5">
          <span className="text-blue-700 dark:text-blue-300 font-medium">
            {getProviderDisplayName(summary.provider)}
          </span>
          
          <div className="w-1 h-1 bg-blue-400 rounded-full"></div>
          
          <span className="text-blue-600 dark:text-blue-400">
            {summary.total_messages} 条对话
          </span>
        </div>

        {/* 清空按钮 */}
        <button
          onClick={async () => {
            try {
              await fetch(
                `${API_BASE}/api/conversation/${projectId}/history?provider=${activeProvider}`,
                { method: 'DELETE' }
              );
              setSummary(null);
              setIsVisible(false);
            } catch (error) {
              console.error('Failed to clear conversation:', error);
            }
          }}
          className="ml-1 text-blue-400 hover:text-blue-600 dark:text-blue-500 dark:hover:text-blue-300 transition-colors"
          title="清空当前AI的对话历史"
        >
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </motion.div>
    </AnimatePresence>
  );
}