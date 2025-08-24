/**
 * CLI Type Definitions
 */

export interface CLIOption {
  id: string;
  name: string;
  description: string;
  icon?: string;
  available: boolean;
  configured: boolean;
  models?: CLIModel[];
  enabled?: boolean;
}

export interface CLIModel {
  id: string;
  name: string;
  description?: string;
}

export interface CLIStatus {
  cli_type: string;
  available: boolean;
  configured: boolean;
  error?: string;
  models?: string[];
}

export interface CLIPreference {
  preferred_cli: string;
  fallback_enabled: boolean;
  selected_model?: string;
}

export const CLI_OPTIONS: CLIOption[] = [
  {
    id: 'claude',
    name: 'Claude',
    description: '',
    available: true,
    configured: false,
    enabled: true,
    models: [
      { id: 'claude-sonnet-4', name: 'Claude Sonnet 4' },
      { id: 'claude-opus-4.1', name: 'Claude Opus 4.1' },
      { id: 'claude-3.5-sonnet', name: 'Claude 3.5 Sonnet' },
      { id: 'claude-3-opus', name: 'Claude 3 Opus' },
      { id: 'claude-3-haiku', name: 'Claude 3 Haiku' }
    ]
  },
  {
    id: 'cursor',
    name: 'Cursor',
    description: '',
    available: true,
    configured: false,
    enabled: true,
    models: [
      { id: 'gpt-5', name: 'GPT-5' },
      { id: 'claude-sonnet-4', name: 'Claude Sonnet 4' },
      { id: 'claude-opus-4.1', name: 'Claude Opus 4.1' },
      { id: 'gpt-4', name: 'GPT-4' },
      { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' }
    ]
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    description: '深度求索代码模型',
    available: true,
    configured: false,
    enabled: true,
    models: [
      { id: 'deepseek-coder', name: 'DeepSeek Coder', description: '专业代码生成模型' },
      { id: 'deepseek-chat', name: 'DeepSeek Chat', description: '通用对话模型' }
    ]
  },
  {
    id: 'qwen',
    name: 'Qwen',
    description: '阿里云通义千问',
    available: true,
    configured: false,
    enabled: true,
    models: [
      { id: 'qwen-max', name: '通义千问-Max', description: '最强大的通用模型' },
      { id: 'qwen-plus', name: '通义千问-Plus', description: '平衡性能和成本' },
      { id: 'qwen2.5-coder-32b-instruct', name: '通义千问-Coder', description: '专业代码生成' },
      { id: 'qwen-turbo', name: '通义千问-Turbo', description: '快速响应模型' }
    ]
  },
  {
    id: 'kimi',
    name: 'Kimi',
    description: '月之暗面Kimi模型',
    available: true,
    configured: false,
    enabled: true,
    models: [
      { id: 'moonshot-v1-8k', name: 'Kimi K2 8K', description: '8K上下文窗口' },
      { id: 'moonshot-v1-32k', name: 'Kimi K2 32K', description: '32K上下文窗口' },
      { id: 'moonshot-v1-128k', name: 'Kimi K2 128K', description: '128K上下文窗口' }
    ]
  },
  {
    id: 'doubao',
    name: 'Doubao',
    description: '字节跳动豆包模型',
    available: true,
    configured: false,
    enabled: true,
    models: [
      { id: 'ep-20241224053255-w6rj2', name: '豆包 Seed', description: '豆包基础模型' },
      { id: 'doubao-pro-4k', name: '豆包 Pro 4K', description: '4K上下文窗口' },
      { id: 'doubao-pro-32k', name: '豆包 Pro 32K', description: '32K上下文窗口' }
    ]
  },
];