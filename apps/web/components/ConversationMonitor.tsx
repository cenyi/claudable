"""
对话历史实时监控面板
显示token使用情况、上下文窗口状态和智能优化信息
"""
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface ConversationStats {
  provider: string;
  total_messages: number;
  estimated_tokens: number;
  context_window: number;
  usage_percentage: number;
  optimization_applied: boolean;
  last_optimization: string | null;
}

interface ConversationMonitorProps {
  projectId: string;
  activeProvider?: string;
  className?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080';

export default function ConversationMonitor({
  projectId,
  activeProvider,
  className = ""
}: ConversationMonitorProps) {
  const [stats, setStats] = useState<ConversationStats[]>([]);
  const [isVisible, setIsVisible] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (projectId) {
      loadConversationStats();
      
      // 设置定期刷新
      const interval = setInterval(loadConversationStats, 30000); // 30秒刷新一次
      setRefreshInterval(interval);
      
      return () => {
        if (interval) clearInterval(interval);
      };
    }
  }, [projectId]);

  const loadConversationStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/conversation/${projectId}/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data.providers || []);
      }
    } catch (error) {
      console.error('Failed to load conversation stats:', error);
    }
  };

  const getUsageColor = (percentage: number) => {
    if (percentage < 50) return 'text-green-600 dark:text-green-400';
    if (percentage < 80) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getUsageBarColor = (percentage: number) => {
    if (percentage < 50) return 'bg-green-500';
    if (percentage < 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
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

  if (stats.length === 0) {
    return null;
  }

  return (
    <div className={`${className}`}>
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        {/* 标题栏 */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <h3 className="text-sm font-medium text-gray-900 dark:text-white">
              对话状态监控
            </h3>
          </div>
          
          <button
            onClick={() => setIsVisible(!isVisible)}
            className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            {isVisible ? '隐藏详情' : '显示详情'}
          </button>
        </div>

        {/* 概览信息 */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {stats.filter(s => s.total_messages > 0).length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">活跃模型</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {formatNumber(stats.reduce((sum, s) => sum + s.estimated_tokens, 0))}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">总Tokens</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {Math.max(...stats.map(s => s.usage_percentage)).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">最高使用率</div>
          </div>
        </div>

        {/* 详细信息 */}
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3"
          >
            {stats.filter(stat => stat.total_messages > 0).map((stat) => (
              <div
                key={stat.provider}
                className={`p-3 rounded-lg border ${
                  activeProvider === stat.provider
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{getProviderIcon(stat.provider)}</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {getProviderDisplayName(stat.provider)}
                    </span>
                    {stat.optimization_applied && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
                        ✨ 已优化
                      </span>
                    )}
                  </div>
                  
                  <div className="text-right">
                    <div className={`text-sm font-medium ${getUsageColor(stat.usage_percentage)}`}>
                      {stat.usage_percentage.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {formatNumber(stat.estimated_tokens)}/{formatNumber(stat.context_window)}
                    </div>
                  </div>
                </div>
                
                {/* 进度条 */}
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full ${getUsageBarColor(stat.usage_percentage)} transition-all duration-300`}
                    style={{ width: `${Math.min(stat.usage_percentage, 100)}%` }}
                  ></div>
                </div>
                
                <div className="mt-2 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                  <span>{stat.total_messages} 条消息</span>
                  {stat.last_optimization && (
                    <span>优化于 {new Date(stat.last_optimization).toLocaleTimeString()}</span>
                  )}
                </div>
              </div>
            ))}
          </motion.div>
        )}

        {/* 智能提示 */}
        {stats.some(s => s.usage_percentage > 80) && (
          <div className="mt-3 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
            <div className="flex items-start gap-2">
              <svg className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div>
                <div className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  上下文使用率较高
                </div>
                <div className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                  系统已自动优化对话历史，保持最相关的内容。如需要，您可以手动清空部分对话历史。
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}