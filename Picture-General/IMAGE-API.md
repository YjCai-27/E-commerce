# 图片生成API集成说明

已经为你的项目添加了**字节跳动豆包API图片生成接口**。现在你不仅可以生成图片提示词，还可以直接调用豆包API生成图片！

## 📁 新增文件

- `image-generator.js` - 图片生成API核心脚本
- `.env.example` - 环境变量配置示例
- `generate-images.bat` - Windows批处理快捷脚本
- `package.json` - 项目配置
- `IMAGE-API.md` - 本说明文件

## 🚀 使用方法

### 1. 配置API密钥

复制 `.env.example` 为 `.env`：
```bash
cp .env.example .env
```

编辑 `.env`，填入你的豆包API密钥：
```env
DOUBO_API_KEY=你的实际API密钥
```

### 2. 使用命令行生成图片

#### 方式一：使用Node直接运行
```bash
# 设置环境变量（Windows CMD）
set DOUBO_API_KEY=你的API密钥
node image-generator.js <提示词文件> [输出目录]

# Windows PowerShell
$env:DOUBO_API_KEY="你的API密钥"
node image-generator.js outputs/ep01-JBL-GO4/02-prompts.md outputs/ep01-JBL-GO4/images
```

#### 方式二：使用批处理脚本（推荐，Windows）
```bash
# 已经配置好.env后，直接运行：
generate-images.bat outputs/ep01-JBL-GO4/02-prompts.md outputs/ep01-JBL-GO4/images
```

### 3. 示例

假设你已经通过原有工作流程生成了 `outputs/ep01-JBL-GO4/02-prompts.md`，想要生成图片：
```bash
generate-images.bat outputs/ep01-JBL-GO4/02-prompts.md outputs/ep01-JBL-GO4/images
```

脚本会：
1. 自动读取提示词文件中所有图片提示词
2. 逐个调用豆包API生成图片
3. 自动下载图片到输出目录

## ⚙️ 可配置参数

在 `image-generator.js` 头部可以修改默认参数：

```javascript
const DEFAULT_PARAMS = {
  width: 1024,      // 图片宽度
  height: 1024,     // 图片高度
  num: 1,          // 每个提示词生成几张图片
  model: "doubao-v2", // 模型版本
  style: "auto"     // 风格：auto, anime, photography, painting, cartoon
};
```

## 🔌 API调用说明

豆包文本生成图片API端点：
- `https://aquasearch.doubao.com/api/v1/text2image`
- 请求头需要携带 `Authorization: Bearer {API_KEY}`
- 返回格式为JSON，包含生成的图片URL数组

## 📝 说明

- 这个脚本使用原生Node.js，不需要额外安装依赖（不需要`npm install`）
- 如果你的豆包API端点不同，可以修改 `DOUBO_API_URL` 常量
- 图片会按提示词标题命名，保存在你指定的输出目录
- 如果API调用失败，会显示错误信息并继续生成下一张

## ❓ 获取豆包API密钥

如果你还没有API密钥，可以前往 [字节跳动开放平台](https://developer.doubao.com/) 申请。
