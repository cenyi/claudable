"use client";
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080';

interface ConversationSummary {
  total_messages: number;
  user_messages: number;
  assistant_messages: number;
  has_system_prompt: boolean;
  provider: string;
}

interface ProviderInfo {
  active: boolean;
  summary: ConversationSummary | null;
}

interface ConversationHistoryTabProps {
  projectId: string;
}

const PROVIDERS = [
  { id: 'deepseek', name: 'DeepSeek', icon: '🔍', color: 'from-blue-500 to-indigo-600' },
  { id: 'qwen', name: '通义千问', icon: '🐉', color: 'from-red-500 to-pink-600' },
  { id: 'kimi', name: 'Kimi', icon: '🌙', color: 'from-purple-500 to-violet-600' },
  { id: 'doubao', name: '豆包', icon: '🫘', color: 'from-green-500 to-teal-600' }
];

export default function ConversationHistoryTab({ projectId }: ConversationHistoryTabProps) {
  const [providersInfo, setProvidersInfo] = useState<Record<string, ProviderInfo>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [clearingProvider, setClearingProvider] = useState<string | null>(null);
  const [actionStatus, setActionStatus] = useState<'idle' | 'success' | 'error'>('idle');

  useEffect(() => {
    loadProvidersInfo();
  }, [projectId]);

  const loadProvidersInfo = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/conversation/${projectId}/providers`);
      if (response.ok) {
        const data = await response.json();
        setProvidersInfo(data);
      } else {
        console.error('Failed to load providers info');
      }
    } catch (error) {
      console.error('Error loading providers info:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const clearConversationHistory = async (provider: string) => {
    const confirmed = confirm(`确定要清空 ${PROVIDERS.find(p => p.id === provider)?.name} 的对话历史吗？此操作不可撤销。`);
    if (!confirmed) return;

    setClearingProvider(provider);
    try {
      const response = await fetch(`${API_BASE}/api/conversation/${projectId}/history?provider=${provider}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setActionStatus('success');
        await loadProvidersInfo(); // 重新加载数据
        setTimeout(() => setActionStatus('idle'), 2000);
      } else {
        setActionStatus('error');
        setTimeout(() => setActionStatus('idle'), 3000);
      }
    } catch (error) {
      console.error('Error clearing conversation history:', error);
      setActionStatus('error');
      setTimeout(() => setActionStatus('idle'), 3000);
    } finally {
      setClearingProvider(null);
    }
  };

  const resetAllConversations = async () => {
    const activeProviders = Object.entries(providersInfo)
      .filter(([_, info]) => info.active)
      .map(([provider, _]) => PROVIDERS.find(p => p.id === provider)?.name)
      .filter(Boolean);

    if (activeProviders.length === 0) {
      alert('没有活跃的对话历史需要清空。');
      return;
    }

    const confirmed = confirm(`确定要清空所有 ${activeProviders.length} 个模型的对话历史吗？\n\n包括：${activeProviders.join('、')}\n\n此操作不可撤销。`);
    if (!confirmed) return;

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/conversation/${projectId}/reset-all`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        setActionStatus('success');
        await loadProvidersInfo(); // 重新加载数据
        setTimeout(() => setActionStatus('idle'), 2000);
      } else {
        setActionStatus('error');
        setTimeout(() => setActionStatus('idle'), 3000);
      }
    } catch (error) {
      console.error('Error resetting all conversations:', error);
      setActionStatus('error');
      setTimeout(() => setActionStatus('idle'), 3000);
    } finally {
      setIsLoading(false);
    }
  };

  const formatConversationInfo = (summary: ConversationSummary | null) => {
    if (!summary || summary.total_messages === 0) {
      return '暂无对话历史';
    }

    return `${summary.total_messages} 条消息 (用户: ${summary.user_messages}, 助手: ${summary.assistant_messages})`;
  };

  return (
    <div className="space-y-6">
      {/* 头部信息 */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">对话历史管理</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            管理国产AI模型的多轮对话历史，清空历史将开始新的对话会话
          </p>
        </div>

        {/* 全局操作按钮 */}
        <div className="flex gap-2">
          <button
            onClick={loadProvidersInfo}
            disabled={isLoading}
            className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            {isLoading ? '刷新中...' : '刷新'}
          </button>
          
          <button
            onClick={resetAllConversations}
            disabled={isLoading || Object.values(providersInfo).every(info => !info.active)}
            className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            清空所有历史
          </button>
        </div>
      </div>

      {/* 状态消息 */}
      {actionStatus !== 'idle' && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className={`p-3 rounded-lg ${
            actionStatus === 'success' 
              ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200' 
              : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'
          }`}
        >
          {actionStatus === 'success' ? '✅ 操作成功完成' : '❌ 操作失败，请重试'}
        </motion.div>
      )}

      {/* 模型列表 */}
      <div className="grid gap-4">
        {PROVIDERS.map((provider) => {
          const info = providersInfo[provider.id];
          const isClearing = clearingProvider === provider.id;
          
          return (
            <motion.div
              key={provider.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg bg-gradient-to-r ${provider.color} flex items-center justify-center text-white text-lg`}>
                    {provider.icon}
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">{provider.name}</h4>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {isLoading ? '加载中...' : formatConversationInfo(info?.summary)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {/* 状态指示 */}
                  <div className={`w-2 h-2 rounded-full ${
                    info?.active ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                  }`} />
                  
                  {/* 清空按钮 */}
                  <button
                    onClick={() => clearConversationHistory(provider.id)}
                    disabled={isLoading || isClearing || !info?.active}
                    className="px-3 py-1 text-sm text-red-600 dark:text-red-400 border border-red-300 dark:border-red-600 rounded hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isClearing ? '清空中...' : '清空历史'}
                  </button>
                </div>
              </div>

              {/* 详细信息 */}
              {info?.summary && info.summary.total_messages > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-lg font-medium text-gray-900 dark:text-white">
                        {info.summary.user_messages}
                      </div>
                      <div className="text-gray-500 dark:text-gray-400">用户消息</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-medium text-gray-900 dark:text-white">
                        {info.summary.assistant_messages}
                      </div>
                      <div className="text-gray-500 dark:text-gray-400">助手回复</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-medium text-gray-900 dark:text-white">
                        {info.summary.has_system_prompt ? '✓' : '✗'}
                      </div>
                      <div className="text-gray-500 dark:text-gray-400">系统提示</div>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* 说明信息 */}
      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div className="flex items-start gap-3">
          <div className="text-blue-500 dark:text-blue-400 mt-0.5">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">
              多轮对话功能说明
            </h4>
            <div className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
              <p>• <strong>多轮对话</strong>：国产AI模型现已支持多轮对话，会记住之前的对话内容</p>
              <p>• <strong>自动管理</strong>：系统会自动管理对话历史长度，超出上下文窗口时会智能截断</p>
              <p>• <strong>独立会话</strong>：每个AI模型的对话历史独立管理，互不影响</p>
              <p>• <strong>清空重置</strong>：清空对话历史后，下次对话将开始新的会话</p>
              <p>• <strong>系统提示</strong>：每个模型都有专门的系统提示，优化代码生成效果</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}