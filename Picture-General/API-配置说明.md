# API密钥配置说明

## 修改API密钥位置

你的豆包API密钥保存在项目根目录的 **`.env`** 文件中。

### 修改方法：

1. 打开文件 `C:\Users\Administrator\Desktop\电商图片直出\.env`
2. 修改 `DOUBO_API_KEY=` 后面的内容
3. 保存文件即可

### 当前配置内容：
```env
# 豆包API配置
DOUBO_API_KEY=06c3ee96-da42-4a88-8660-2acf217146f6

# 默认图片生成参数
DEFAULT_WIDTH=1024
DEFAULT_HEIGHT=1024
DEFAULT_MODEL=doubao-seedream-5-0-260128
DEFAULT_STYLE=auto
```

### 修改示例：
如果你要改成新密钥 `abc123-xxx-xxx`，修改后：
```env
DOUBO_API_KEY=abc123-xxx-xxx
```

---

## 验证配置

修改后可以用命令验证：
```bash
cd C:\Users\Administrator\Desktop\电商图片直出
cat .env
```
就能看到当前配置的密钥了。
