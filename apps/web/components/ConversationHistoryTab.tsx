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
  { id: 'qwen', name: 'Qwen', icon: '🐉', color: 'from-red-500 to-pink-600' },
  { id: 'kimi', name: 'Kimi', icon: '🌙', color: 'from-purple-500 to-violet-600' },
  { id: 'doubao', name: 'Doubao', icon: '🫘', color: 'from-green-500 to-teal-600' }
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
    const confirmed = confirm(`Are you sure you want to clear the conversation history for ${PROVIDERS.find(p => p.id === provider)?.name}? This action cannot be undone.`);
    if (!confirmed) return;

    setClearingProvider(provider);
    try {
      const response = await fetch(`${API_BASE}/api/conversation/${projectId}/history?provider=${provider}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setActionStatus('success');
        await loadProvidersInfo(); // Reload data
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
      alert('No active conversation history to clear.');
      return;
    }

    const confirmed = confirm(`Are you sure you want to clear conversation history for all ${activeProviders.length} models?\n\nIncluding: ${activeProviders.join(', ')}\n\nThis action cannot be undone.`);
    if (!confirmed) return;

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/conversation/${projectId}/reset-all`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        setActionStatus('success');
        await loadProvidersInfo(); // Reload data
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
      return 'No conversation history';
    }

    return `${summary.total_messages} messages (User: ${summary.user_messages}, Assistant: ${summary.assistant_messages})`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Conversation History Management</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Manage multi-turn conversation history for domestic AI models. Clearing history will start a new conversation session.
          </p>
        </div>

        {/* Global actions */}
        <div className="flex gap-2">
          <button
            onClick={loadProvidersInfo}
            disabled={isLoading}
            className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>
          
          <button
            onClick={resetAllConversations}
            disabled={isLoading || Object.values(providersInfo).every(info => !info.active)}
            className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Clear All History
          </button>
        </div>
      </div>

      {/* Status messages */}
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
          {actionStatus === 'success' ? '✅ Operation completed successfully' : '❌ Operation failed, please try again'}
        </motion.div>
      )}

      {/* Model list */}
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
                      {isLoading ? 'Loading...' : formatConversationInfo(info?.summary)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {/* Status indicator */}
                  <div className={`w-2 h-2 rounded-full ${
                    info?.active ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                  }`} />
                  
                  {/* Clear button */}
                  <button
                    onClick={() => clearConversationHistory(provider.id)}
                    disabled={isLoading || isClearing || !info?.active}
                    className="px-3 py-1 text-sm text-red-600 dark:text-red-400 border border-red-300 dark:border-red-600 rounded hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isClearing ? 'Clearing...' : 'Clear History'}
                  </button>
                </div>
              </div>

              {/* Detailed information */}
              {info?.summary && info.summary.total_messages > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-lg font-medium text-gray-900 dark:text-white">
                        {info.summary.user_messages}
                      </div>
                      <div className="text-gray-500 dark:text-gray-400">User Messages</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-medium text-gray-900 dark:text-white">
                        {info.summary.assistant_messages}
                      </div>
                      <div className="text-gray-500 dark:text-gray-400">Assistant Replies</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-medium text-gray-900 dark:text-white">
                        {info.summary.has_system_prompt ? '✓' : '✗'}
                      </div>
                      <div className="text-gray-500 dark:text-gray-400">System Prompt</div>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Instructions */}
      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div className="flex items-start gap-3">
          <div className="text-blue-500 dark:text-blue-400 mt-0.5">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">
              Multi-turn Conversation Features
            </h4>
            <div className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
              <p>• <strong>Multi-turn Conversations</strong>: Domestic AI models now support multi-turn conversations and will remember previous conversation content</p>
              <p>• <strong>Automatic Management</strong>: The system automatically manages conversation history length and intelligently truncates when exceeding the context window</p>
              <p>• <strong>Independent Sessions</strong>: Each AI model's conversation history is managed independently without affecting each other</p>
              <p>• <strong>Clear and Reset</strong>: After clearing conversation history, the next conversation will start a new session</p>
              <p>• <strong>System Prompts</strong>: Each model has a dedicated system prompt to optimize code generation results</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}