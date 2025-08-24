#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rootDir = path.join(__dirname, '..');
const envFile = path.join(rootDir, '.env');
const envExampleFile = path.join(rootDir, '.env.example');

console.log('🚀 Claudable 国产AI大模型配置助手');
console.log('==================================\n');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// 询问用户输入
function askQuestion(question) {
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      resolve(answer.trim());
    });
  });
}

// 验证API密钥格式
function validateApiKey(provider, key) {
  if (!key) return true; // 空值跳过
  
  switch (provider) {
    case 'deepseek':
      return key.startsWith('sk-');
    case 'qwen':
      return key.startsWith('sk-');
    case 'kimi':
      return key.startsWith('sk-');
    case 'doubao':
      return key.length > 10; // 豆包的密钥格式不固定
    default:
      return true;
  }
}

// 读取现有环境变量
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

// 写入环境变量
function writeEnvFile(envVars) {
  const lines = [
    '# Claudable Environment Variables',
    '# 自动生成的配置文件',
    '',
    '# ===========================================',
    '# 国产AI大模型API配置',
    '# ===========================================',
    ''
  ];

  // 添加国产模型配置
  if (envVars.DEEPSEEK_API_KEY) {
    lines.push('# DeepSeek API配置');
    lines.push(`DEEPSEEK_API_KEY=${envVars.DEEPSEEK_API_KEY}`);
    lines.push('');
  }

  if (envVars.QWEN_API_KEY) {
    lines.push('# 通义千问API配置');
    lines.push(`QWEN_API_KEY=${envVars.QWEN_API_KEY}`);
    lines.push('');
  }

  if (envVars.KIMI_API_KEY) {
    lines.push('# Kimi API配置');
    lines.push(`KIMI_API_KEY=${envVars.KIMI_API_KEY}`);
    lines.push('');
  }

  if (envVars.DOUBAO_API_KEY) {
    lines.push('# 豆包API配置');
    lines.push(`DOUBAO_API_KEY=${envVars.DOUBAO_API_KEY}`);
    lines.push('');
  }

  // 添加其他现有配置
  const otherKeys = Object.keys(envVars).filter(key => 
    !['DEEPSEEK_API_KEY', 'QWEN_API_KEY', 'KIMI_API_KEY', 'DOUBAO_API_KEY'].includes(key)
  );

  if (otherKeys.length > 0) {
    lines.push('# ===========================================');
    lines.push('# 其他配置');
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
    console.log('此工具将帮助您配置国产AI大模型的API密钥。');
    console.log('您可以选择配置一个或多个模型，也可以稍后手动配置。\n');

    const existingEnv = readExistingEnv();
    
    // DeepSeek配置
    console.log('📘 DeepSeek (深度求索)');
    console.log('获取API密钥: https://platform.deepseek.com/api_keys');
    const currentDeepSeek = existingEnv.DEEPSEEK_API_KEY || '';
    if (currentDeepSeek) {
      console.log(`当前配置: ${currentDeepSeek.substring(0, 10)}...`);
    }
    const deepseekKey = await askQuestion('请输入DeepSeek API密钥 (直接回车跳过): ');
    
    if (deepseekKey && !validateApiKey('deepseek', deepseekKey)) {
      console.log('⚠️  DeepSeek API密钥格式错误，应以sk-开头');
    } else if (deepseekKey) {
      existingEnv.DEEPSEEK_API_KEY = deepseekKey;
      console.log('✅ DeepSeek API密钥已设置');
    }
    console.log('');

    // 通义千问配置
    console.log('📗 通义千问 (阿里云百炼)');
    console.log('获取API密钥: https://bailian.console.aliyun.com/');
    const currentQwen = existingEnv.QWEN_API_KEY || '';
    if (currentQwen) {
      console.log(`当前配置: ${currentQwen.substring(0, 10)}...`);
    }
    const qwenKey = await askQuestion('请输入通义千问API密钥 (直接回车跳过): ');
    
    if (qwenKey && !validateApiKey('qwen', qwenKey)) {
      console.log('⚠️  通义千问API密钥格式错误，应以sk-开头');
    } else if (qwenKey) {
      existingEnv.QWEN_API_KEY = qwenKey;
      console.log('✅ 通义千问API密钥已设置');
    }
    console.log('');

    // Kimi配置
    console.log('📙 Kimi (月之暗面)');
    console.log('获取API密钥: https://platform.moonshot.cn/console/api-keys');
    const currentKimi = existingEnv.KIMI_API_KEY || '';
    if (currentKimi) {
      console.log(`当前配置: ${currentKimi.substring(0, 10)}...`);
    }
    const kimiKey = await askQuestion('请输入Kimi API密钥 (直接回车跳过): ');
    
    if (kimiKey && !validateApiKey('kimi', kimiKey)) {
      console.log('⚠️  Kimi API密钥格式错误，应以sk-开头');
    } else if (kimiKey) {
      existingEnv.KIMI_API_KEY = kimiKey;
      console.log('✅ Kimi API密钥已设置');
    }
    console.log('');

    // 豆包配置
    console.log('📕 豆包 (字节跳动)');
    console.log('获取API密钥: https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey');
    const currentDoubao = existingEnv.DOUBAO_API_KEY || '';
    if (currentDoubao) {
      console.log(`当前配置: ${currentDoubao.substring(0, 10)}...`);
    }
    const doubaoKey = await askQuestion('请输入豆包API密钥 (直接回车跳过): ');
    
    if (doubaoKey) {
      existingEnv.DOUBAO_API_KEY = doubaoKey;
      console.log('✅ 豆包API密钥已设置');
    }
    console.log('');

    // 写入配置文件
    writeEnvFile(existingEnv);
    
    console.log('🎉 配置完成！');
    console.log(`配置文件已保存到: ${envFile}`);
    console.log('');
    console.log('📝 下一步:');
    console.log('1. 运行 npm run dev 启动Claudable');
    console.log('2. 在项目设置中选择您配置的AI模型');
    console.log('3. 开始使用国产AI大模型进行代码生成！');
    console.log('');
    console.log('💡 提示: 您可以随时运行此脚本更新API密钥配置');

  } catch (error) {
    console.error('❌ 配置过程中出现错误:', error);
  } finally {
    rl.close();
  }
}

main();