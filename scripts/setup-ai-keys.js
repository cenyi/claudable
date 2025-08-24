#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rootDir = path.join(__dirname, '..');
const envFile = path.join(rootDir, '.env');
const envExampleFile = path.join(rootDir, '.env.example');

console.log('🚀 Claudable Domestic AI Model Configuration Assistant');
console.log('==================================\n');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Ask for user input
function askQuestion(question) {
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      resolve(answer.trim());
    });
  });
}

// Validate API key format
function validateApiKey(provider, key) {
  if (!key) return true; // Skip empty values
  
  switch (provider) {
    case 'deepseek':
      return key.startsWith('sk-');
    case 'qwen':
      return key.startsWith('sk-');
    case 'kimi':
      return key.startsWith('sk-');
    case 'doubao':
      return key.length > 10; // Doubao key format is not fixed
    default:
      return true;
  }
}

// Read existing environment variables
function readExistingEnv() {
  const envVars = {};
  if (fs.existsSync(envFile)) {
    const content = fs.readFileSync(envFile, 'utf8');
    const lines = content.split('\n');
    for (const line of lines) {
      const match = line.match(/^([A-Z_]+)=(.*)$/);
      if (match) {
        envVars[match[1]] = match[2];
      }
    }
  }
  return envVars;
}

// Write environment variables
function writeEnvFile(envVars) {
  const lines = [
    '# Claudable Environment Variables',
    '# Auto-generated configuration file',
    '',
    '# ===========================================',
    '# Domestic AI Model API Configuration',
    '# ===========================================',
    ''
  ];

  // Add domestic model configuration
  if (envVars.DEEPSEEK_API_KEY) {
    lines.push('# DeepSeek API Configuration');
    lines.push(`DEEPSEEK_API_KEY=${envVars.DEEPSEEK_API_KEY}`);
    lines.push('');
  }

  if (envVars.QWEN_API_KEY) {
    lines.push('# Qwen API Configuration');
    lines.push(`QWEN_API_KEY=${envVars.QWEN_API_KEY}`);
    lines.push('');
  }

  if (envVars.KIMI_API_KEY) {
    lines.push('# Kimi API Configuration');
    lines.push(`KIMI_API_KEY=${envVars.KIMI_API_KEY}`);
    lines.push('');
  }

  if (envVars.DOUBAO_API_KEY) {
    lines.push('# Doubao API Configuration');
    lines.push(`DOUBAO_API_KEY=${envVars.DOUBAO_API_KEY}`);
    lines.push('');
  }

  // Add other existing configurations
  const otherKeys = Object.keys(envVars).filter(key => 
    !['DEEPSEEK_API_KEY', 'QWEN_API_KEY', 'KIMI_API_KEY', 'DOUBAO_API_KEY'].includes(key)
  );

  if (otherKeys.length > 0) {
    lines.push('# ===========================================');
    lines.push('# Other Configuration');
    lines.push('# ===========================================');
    lines.push('');
    
    for (const key of otherKeys) {
      lines.push(`${key}=${envVars[key]}`);
    }
  }

  fs.writeFileSync(envFile, lines.join('\n'));
}

async function main() {
  try {
    console.log('This tool will help you configure API keys for domestic AI models.');
    console.log('You can choose to configure one or more models, or configure manually later.\n');

    const existingEnv = readExistingEnv();
    
    // DeepSeek configuration
    console.log('📘 DeepSeek (Deep Seek)');
    console.log('Get API Key: https://platform.deepseek.com/api_keys');
    const currentDeepSeek = existingEnv.DEEPSEEK_API_KEY || '';
    if (currentDeepSeek) {
      console.log(`Current configuration: ${currentDeepSeek.substring(0, 10)}...`);
    }
    const deepseekKey = await askQuestion('Please enter DeepSeek API key (press Enter to skip): ');
    
    if (deepseekKey && !validateApiKey('deepseek', deepseekKey)) {
      console.log('⚠️  DeepSeek API key format error, should start with sk-');
    } else if (deepseekKey) {
      existingEnv.DEEPSEEK_API_KEY = deepseekKey;
      console.log('✅ DeepSeek API key has been set');
    }
    console.log('');

    // Qwen configuration
    console.log('📗 Qwen (Alibaba Cloud Bailian)');
    console.log('Get API Key: https://bailian.console.aliyun.com/');
    const currentQwen = existingEnv.QWEN_API_KEY || '';
    if (currentQwen) {
      console.log(`Current configuration: ${currentQwen.substring(0, 10)}...`);
    }
    const qwenKey = await askQuestion('Please enter Qwen API key (press Enter to skip): ');
    
    if (qwenKey && !validateApiKey('qwen', qwenKey)) {
      console.log('⚠️  Qwen API key format error, should start with sk-');
    } else if (qwenKey) {
      existingEnv.QWEN_API_KEY = qwenKey;
      console.log('✅ Qwen API key has been set');
    }
    console.log('');

    // Kimi configuration
    console.log('📙 Kimi (Moonshot AI)');
    console.log('Get API Key: https://platform.moonshot.cn/console/api-keys');
    const currentKimi = existingEnv.KIMI_API_KEY || '';
    if (currentKimi) {
      console.log(`Current configuration: ${currentKimi.substring(0, 10)}...`);
    }
    const kimiKey = await askQuestion('Please enter Kimi API key (press Enter to skip): ');
    
    if (kimiKey && !validateApiKey('kimi', kimiKey)) {
      console.log('⚠️  Kimi API key format error, should start with sk-');
    } else if (kimiKey) {
      existingEnv.KIMI_API_KEY = kimiKey;
      console.log('✅ Kimi API key has been set');
    }
    console.log('');

    // Doubao configuration
    console.log('📕 Doubao (ByteDance)');
    console.log('Get API Key: https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey');
    const currentDoubao = existingEnv.DOUBAO_API_KEY || '';
    if (currentDoubao) {
      console.log(`Current configuration: ${currentDoubao.substring(0, 10)}...`);
    }
    const doubaoKey = await askQuestion('Please enter Doubao API key (press Enter to skip): ');
    
    if (doubaoKey) {
      existingEnv.DOUBAO_API_KEY = doubaoKey;
      console.log('✅ Doubao API key has been set');
    }
    console.log('');

    // Write configuration file
    writeEnvFile(existingEnv);
    
    console.log('🎉 Configuration completed!');
    console.log(`Configuration file has been saved to: ${envFile}`);
    console.log('');
    console.log('📝 Next steps:');
    console.log('1. Run npm run dev to start Claudable');
    console.log('2. Select your configured AI model in project settings');
    console.log('3. Start using domestic AI models for code generation!');
    
    rl.close();
  } catch (error) {
    console.error('❌ Configuration failed:', error.message);
    rl.close();
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}