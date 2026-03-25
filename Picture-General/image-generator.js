/**
 * 字节跳动豆包API 图片生成接口
 * 用法：node image-generator.js <prompt-file> [output-dir] [product-image-path]
 * 环境变量：DOUBO_API_KEY - 你的豆包API密钥
 *
 * 功能：支持text2img和img2img（参考产品图片生成）
 * 如果找到 product-information 中的对应产品图片，会自动使用img2img让AI参考产品外观
 */

// 加载.env环境变量
require('dotenv').config();

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// 配置豆包API - 火山引擎官方端点
const DOUBO_API_URL = 'https://ark.cn-beijing.volces.com/api/v3/images/generations';
const API_KEY = process.env.DOUBO_API_KEY || '';

// 默认生成参数（按官方文档配置）
// API要求最小总像素 3,686,400
// 电商主图推荐 1600x2304 竖版（正好满足像素要求：1600 * 2304 = 3,686,400）
const DEFAULT_PARAMS = {
  model: "doubao-seedream-5-0-260128",  // 豆包SeeDream 5.0模型
  prompt: "",                           // 提示词，由调用方填充
  sequential_image_generation: "disabled",
  response_format: "url",              // 返回URL格式
  size: "1600x2304",                   // 电商主图竖版（满足最小像素要求）
  stream: false,
  watermark: false,
  // img2img参数 - 如果有产品参考图片会自动启用
  // strength: 0.6,  // 参考强度，0-1，越大越接近原图
};

// 尺寸映射表
const SIZE_MAP = {
  "1K": "1024x1024",
  "2K": "2048x2048",
  "1600x2304": "1600x2304",  // 电商竖版 (满足像素要求)
  "2304x1600": "2304x1600",  // 横版
  "2048x2048": "2048x2048",  // 方形2K
  "1024x1024": "1024x1024"
};

/**
 * 从文件读取提示词
 */
function readPrompts(promptFile) {
  const content = fs.readFileSync(promptFile, 'utf-8');
  // 按图片分割提示词（每个图片用##开头）
  const lines = content.split('\n');
  const prompts = [];
  let currentPrompt = [];

  for (const line of lines) {
    // 捕获##开头的图片，跳过开头的全案说明
    if (line.startsWith('## ') && !line.includes('全案统一风格说明')) {
      if (currentPrompt.length > 0) {
        const joined = currentPrompt.join('\n').trim();
        if (joined.length > 100) {  // 只保存有实际内容的提示词
          prompts.push(joined);
        }
        currentPrompt = [];
      }
    }
    currentPrompt.push(line);
  }
  // 添加最后一个
  if (currentPrompt.length > 0) {
    const joined = currentPrompt.join('\n').trim();
    if (joined.length > 100) {
      prompts.push(joined);
    }
  }

  return prompts;
}

/**
 * 查找产品参考图片 - 在product-information目录中查找匹配产品编号的图片
 */
function findProductReferenceImage(productId) {
  const productDir = path.join(process.cwd(), 'product-information');
  if (!fs.existsSync(productDir)) {
    return null;
  }

  // 支持的图片格式
  const extensions = ['.jpg', '.jpeg', '.png', '.webp', '.JPG', '.PNG'];

  // 查找匹配productId的图片文件
  const files = fs.readdirSync(productDir);
  for (const file of files) {
    const ext = path.extname(file);
    if (extensions.includes(ext) && file.includes(productId)) {
      const fullPath = path.join(productDir, file);
      console.log(`   ✓ 找到产品参考图片: product-information/${file}`);
      // 读取并转为base64
      const imageBuffer = fs.readFileSync(fullPath);
      const base64 = imageBuffer.toString('base64');
      return base64;
    }
  }

  console.log(`   ⚠️  未找到product-information中匹配${productId}的参考图片，使用纯文本生成`);
  return null;
}

/**
 * 将图片转为base64 data URL
 */
function encodeImageToBase64(imageBuffer) {
  return `data:image/png;base64,${imageBuffer.toString('base64')}`;
}

/**
 * 调用豆包API生成图片 - 火山引擎官方格式
 * 如果提供了productImageBase64，则使用img2img参考产品图片生成
 */
async function generateImage(prompt, productImageBase64 = null, params = {}) {
  // 电商图片默认用竖版 1600x2304（适合拼多多/淘宝主图）
  const requestParams = {
    ...DEFAULT_PARAMS,
    ...params,
    prompt
  };

  // 如果有产品参考图片，启用img2img模式
  if (productImageBase64) {
    requestParams.image = `data:image/png;base64,${productImageBase64}`;
    requestParams.strength = 0.6;  // 参考强度：0.6平衡还原度和创作空间
  }

  return new Promise((resolve, reject) => {
    const url = new URL(DOUBO_API_URL);
    const postData = JSON.stringify(requestParams);

    const options = {
      hostname: url.hostname,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          // 火山引擎API返回格式: { created: 123, data: [...], ... }
          if (result.data && Array.isArray(result.data)) {
            // 每个data项有 url 字段
            const imageUrls = result.data.map(item => item.url);
            resolve(imageUrls);
          } else if (result.error) {
            reject(new Error(result.error.message || 'API调用失败'));
          } else {
            console.log('API响应:', JSON.stringify(result, null, 2));
            reject(new Error('API返回格式异常'));
          }
        } catch (e) {
          reject(new Error(`解析响应失败: ${e.message}, 响应内容: ${data.substring(0, 200)}`));
        }
      });
    });

    req.on('error', (err) => {
      reject(new Error(`请求失败: ${err.message}`));
    });

    req.write(postData);
    req.end();
  });
}

/**
 * 下载图片到本地
 */
async function downloadImage(imageUrl, outputPath) {
  return new Promise((resolve, reject) => {
    const protocol = imageUrl.startsWith('https') ? https : http;
    protocol.get(imageUrl, (res) => {
      const fileStream = fs.createWriteStream(outputPath);
      res.pipe(fileStream);
      fileStream.on('finish', () => {
        fileStream.close();
        resolve(outputPath);
      });
      fileStream.on('error', reject);
    }).on('error', reject);
  });
}

/**
 * 主函数
 */
async function main() {
  // 检查API密钥
  if (!API_KEY) {
    console.error('❌ 错误：请设置环境变量 DOUBO_API_KEY');
    console.error('   示例：set DOUBO_API_KEY=your-api-key && node image-generator.js prompts.md outputs');
    process.exit(1);
  }

  // 获取参数
  const promptFile = process.argv[2];
  let outputDir = process.argv[3] || 'outputs/generated';

  if (!promptFile) {
    console.log('📷 豆包图片生成器');
    console.log('用法: node image-generator.js <prompt-file> [output-dir]');
    console.log('');
    console.log('参数:');
    console.log('  prompt-file  - 包含提示词的Markdown文件');
    console.log('  output-dir   - 输出目录（默认: outputs/generated）');
    console.log('');
    console.log('环境变量:');
    console.log('  DOUBO_API_KEY - 豆包API密钥（必需）');
    console.log('');
    console.log('示例:');
    console.log('  set DOUBO_API_KEY=sk-xxx');
    console.log('  node image-generator.js outputs/ep01-JBL-GO4/02-prompts.md outputs/ep01-JBL-GO4/images');
    process.exit(0);
  }

  // 检查提示词文件是否存在
  if (!fs.existsSync(promptFile)) {
    console.error(`❌ 错误：提示词文件不存在: ${promptFile}`);
    process.exit(1);
  }

  // 创建输出目录
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // 读取提示词
  console.log(`📖 读取提示词文件: ${promptFile}`);
  const prompts = readPrompts(promptFile);
  console.log(`✓ 读取到 ${prompts.length} 条提示词`);

  // 从提示词路径提取产品ID (如 outputs/ep01/xxx.md → ep01)
  let productId = path.basename(path.dirname(promptFile));
  console.log(`🔍 查找产品参考图片，产品ID: ${productId}`);
  const productImageBase64 = findProductReferenceImage(productId);
  console.log('');

  // 逐个生成图片
  for (let i = 0; i < prompts.length; i++) {
    const prompt = prompts[i];
    const imageNum = i + 1;
    console.log(`🖼️  正在生成第 ${imageNum} 张图片...`);

    try {
      // 提取标题和提示词（假设第一行是标题）
      const lines = prompt.split('\n').filter(l => l.trim());
      let cleanPrompt = prompt;
      let title = `image-${imageNum}`;

      if (lines.length > 0 && lines[0].startsWith('#')) {
        title = lines[0].replace(/^#+\s*/, '').trim().replace(/[\\/:*?"<>|]/g, '-');
        cleanPrompt = lines.slice(1).join('\n').trim();
      }

      console.log(`   提示词: ${cleanPrompt.substring(0, 100)}...`);

      // 调用API生成 - 如果有产品参考图片，使用img2img
      const images = await generateImage(cleanPrompt, productImageBase64);

      // 下载图片
      for (let j = 0; j < images.length; j++) {
        const imageUrl = images[j];
        const ext = path.extname(new URL(imageUrl).pathname) || '.png';
        const outputFile = path.join(outputDir, `${title}${ext}`);
        await downloadImage(imageUrl, outputFile);
        console.log(`   ✓ 已保存: ${outputFile}`);
      }

      console.log('');
    } catch (error) {
      console.error(`   ❌ 生成失败: ${error.message}`);
      console.log('');
    }
  }

  console.log('🎉 所有图片生成完成！');
  console.log(`📂 输出目录: ${outputDir}`);
}

// 错误处理
process.on('unhandledRejection', (error) => {
  console.error('❌ 未处理的错误:', error.message);
  process.exit(1);
});

// 运行
if (require.main === module) {
  main();
}

// 导出模块供其他代码调用
module.exports = {
  generateImage,
  downloadImage,
  readPrompts
};
