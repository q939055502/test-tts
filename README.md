# Edge-TTS API 服务

## 一、简介

这是一个基于Flask和Edge-TTS的文本转语音API服务，支持多种中文语音模型和语速调整。Edge-TTS是微软基于其Edge浏览器内置的语音合成技术开发的免费开源库，提供业界领先的神经网络语音合成能力。

## 二、功能特点

- RESTful API接口设计
- 支持多种中文语音模型
- 可自定义语速、音调和音量
- 服务层和接口层分离
- Docker容器化部署
- 支持流式语音输出
- 支持SSML高级语音控制

## 三、项目结构

```
├── app.py                # Flask API接口层
├── tts_service.py        # TTS语音生成服务层
├── requirements.txt      # 项目依赖
├── Dockerfile            # Docker构建配置
├── .gitignore            # Git忽略文件配置
└── 语音列表/              # 生成的语音文件保存目录
```

## 四、快速开始

### 手动使用Docker运行

直接使用Docker命令构建和运行容器：

1. **构建Docker镜像**

   ```bash
   docker build -t edge-tts-api .
   ```

2. **运行Docker容器**

   ```bash
   docker run -d -p 5001:5001 --name edge-tts-container --env API_KEY="4b7c9e2a-3d8f-5a1b-6c4d-7e8f9a0b1c2d" edge-tts-api
   ```

3. **带文件挂载运行**

   ```bash
   docker run -d -p 5001:5001 -v ${PWD}/output:/app/output --name edge-tts-container edge-tts-api
   ```

4. **查看容器运行状态**

   ```bash
   docker ps -a | grep edge-tts-container
   ```

5. **停止容器**

   ```bash
   docker stop edge-tts-container
   ```

6. **删除容器**

   ```bash
   docker rm edge-tts-container
   ```

7. **删除镜像**

   ```bash
   docker rmi edge-tts-api
   ```

8. **查看容器日志**

   ```bash
   docker logs edge-tts-container
   # 实时查看日志
   docker logs -f edge-tts-container
   ```

### 配置参数

您可以在运行容器时通过环境变量自定义以下参数：

- **API_KEY**: API密钥，建议在生产环境中修改为更安全的值
- **ALLOWED_IPS**: IP白名单，格式为逗号分隔的IP列表，留空表示不限制

例如：

```bash
# 自定义API密钥和IP白名单
docker run -d -p 5001:5001 --name edge-tts-container \
  --env API_KEY="your-secure-api-key" \
  --env ALLOWED_IPS="192.168.1.100,172.17.0.1" \
  edge-tts-api

# 修改主机端口映射
docker run -d -p 8080:5000 --name edge-tts-container \
  edge-tts-api
```

### 直接本地运行

1. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

2. **启动服务**

   ```bash
   python app.py
   ```

## 五、安全机制

API服务包含以下安全机制，确保服务的安全访问：

### API密钥认证

所有敏感接口（除首页和健康检查外）都需要通过API密钥认证。客户端需要在请求头中包含 `X-API-Key` 字段，值为有效的API密钥。

默认API密钥：`4b7c9e2a-3d8f-5a1b-6c4d-7e8f9a0b1c2d`（请在生产环境中更换）

### IP白名单

可配置IP白名单，限制只有特定IP地址才能访问API。默认不限制IP（`ALLOWED_IPS = []`）。

#### Docker容器中的localhost注意事项

在Docker容器环境中，有一个重要的特殊情况需要注意：

- 在容器内部，`localhost`（127.0.0.1）指的是容器本身，而不是宿主机的localhost
- 从宿主机访问容器时，容器看到的是宿主机在Docker网络中的IP地址（通常是172.17.0.1或类似地址）

#### 正确配置方法

1. **在Dockerfile中**：
   - 不要在Dockerfile中设置localhost作为允许的IP，因为这不会允许从宿主机访问
   - 保持默认值`ENV ALLOWED_IPS=`不变，这样容器默认不限制IP访问

2. **运行容器时**：
   - 通过`--env`参数动态设置允许的IP列表
   - 示例：`docker run -d -p 5001:5001 --name tts-container --env ALLOWED_IPS="192.168.1.100,172.17.0.1" tts-api`
   - 其中`172.17.0.1`通常是宿主机在Docker网络中的IP地址（根据你的网络配置可能有所不同）

### 配置方法

在生产环境中，建议：
1. 从环境变量或配置文件中读取敏感配置
2. 配置IP白名单，限制访问来源

## 六、API接口说明

### 1. 首页

- **URL**: `/`
- **方法**: GET
- **描述**: 服务信息介绍
- **返回**: 服务版本和可用接口信息

### 2. 健康检查

- **URL**: `/api/health`
- **方法**: GET
- **描述**: 检查服务是否正常运行
- **返回**: 服务状态信息

### 3. 获取可用语音列表

- **URL**: `/api/voices`
- **方法**: GET
- **描述**: 获取所有可用的中文语音模型
- **返回**: 语音模型列表

### 4. 生成语音

- **URL**: `/api/tts`
- **方法**: POST
- **描述**: 将文本转换为语音
- **参数** (JSON):
  - `text` (必需): 要转换为语音的文本
  - `voice` (可选): 语音模型，默认为"zh-CN-YunxiNeural"
  - `rate` (可选): 语速，默认为"+0%"
- **查询参数**:
  - `return_json=true`: 设置为true时返回JSON结果，否则直接返回语音文件
- **返回**: 语音文件或JSON结果信息

### 5. 流式语音输出

- **URL**: `/api/tts/stream`
- **方法**: POST
- **描述**: 流式输出语音数据
- **参数** (JSON):
  - `text` (必需): 要转换为语音的文本
  - `voice` (可选): 语音模型，默认为"zh-CN-YunxiNeural"
  - `rate` (可选): 语速，默认为"+0%"
- **返回**: 流式音频数据

## 七、使用示例

### 获取语音列表

```bash
curl http://localhost:5000/api/voices
```

### 生成语音（返回文件）

```bash
curl -X POST -H "Content-Type: application/json" -d '{"text":"你好，这是一段测试文本"}' http://localhost:5000/api/tts --output output.mp3
```

### 生成语音（返回JSON）

```bash
curl -X POST -H "Content-Type: application/json" -d '{"text":"你好，这是一段测试文本", "voice":"zh-CN-YunyangNeural", "rate":"+10%"}' http://localhost:5000/api/tts?return_json=true
```

### 使用API密钥认证

```bash
curl -X POST http://localhost:5000/api/tts -H "X-API-Key: 4b7c9e2a-3d8f-5a1b-6c4d-7e8f9a0b1c2d" -H "Content-Type: application/json" -d '{"text": "你好，这是一段测试文本"}'
```

## 八、Edge-TTS 库详解

### 基本介绍

Edge-TTS 是微软基于其 Edge 浏览器内置的语音合成技术开发的免费开源库，提供业界领先的神经网络语音合成能力。它允许开发者将文本转换为自然流畅的语音，支持多种语言和声音选择。

### 命令行参数

Edge-TTS 提供了丰富的命令行参数，用于控制语音合成的各个方面：

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--text` | `-t` | 要转换的文本内容 | `--text "你好，世界！"` |
| `--write-media` | `-f` | 输出的音频文件名 | `--write-media output.mp3` |
| `--voice` | `-v` | 选择语音模型 | `--voice zh-CN-XiaoxiaoNeural` |
| `--rate` | `-r` | 语速调节（百分比） | `--rate "+10%"` 或 `--rate "-50%"` |
| `--volume` | | 音量调节（百分比） | `--volume "+20%"` |
| `--pitch` | | 音调调节（百分比） | `--pitch "+5%"` |
| `--write-subtitles` | | 输出字幕文件 | `--write-subtitles output.vtt` |
| `--list-voices` | `-l` | 列出所有可用的语音模型 | `--list-voices` |

### Python 代码调用

#### 基础用法：文本转 MP3 文件

```python
import asyncio
from edge_tts import Communicate

async def text_to_speech():
    # 创建 Communicate 对象
    communicate = Communicate(
        text="微软Edge TTS提供卓越的语音合成体验",
        voice="zh-CN-XiaoxiaoNeural",  # 选择语音
        rate="+10%",  # 语速调整
        volume="+0%"  # 音量调整
    )
    
    # 保存为 MP3 文件
    await communicate.save("output.mp3")

# 运行异步函数
asyncio.run(text_to_speech())
```

#### 实时语音流播放

```python
import asyncio
from edge_tts import Communicate

async def live_tts():
    communicate = Communicate(
        text="正在实时播放合成语音",
        voice="zh-CN-YunxiNeural"
    )
    
    # 流式获取音频数据
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            # 此处可连接音频设备实时输出音频数据
            pass
        elif chunk["type"] == "WordBoundary":
            # 处理单词边界事件
            print(f"单词边界: {chunk['offset']}ms")

asyncio.run(live_tts())
```

### 高级功能：SSML 支持

Edge-TTS 支持 Speech Synthesis Markup Language (SSML)，允许更精细地控制语音合成过程：

```python
import asyncio
from edge_tts import Communicate

async def ssml_example():
    ssml_text = """
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
        <voice name="zh-CN-XiaoxiaoNeural">
            这是正常语速的文本。
            <break time="500ms"/>
            这是暂停了500毫秒后的文本。
            <prosody rate="+30%">这是加速30%的文本。</prosody>
            <prosody volume="+20%">这是音量增加20%的文本。</prosody>
            <prosody pitch="+10%">这是音调提高10%的文本。</prosody>
        </voice>
    </speak>
    """
    
    communicate = Communicate(text=ssml_text, voice="zh-CN-XiaoxiaoNeural")
    await communicate.save("ssml_output.mp3")

asyncio.run(ssml_example())
```

### 最佳实践

1. **处理长文本**：对于较长的文本，建议分段处理，避免一次性生成过长的音频文件

2. **错误处理**：在实际应用中，应考虑网络问题和 API 调用失败的情况，添加相应的错误处理逻辑

3. **选择合适的语音和语速**：根据应用场景和用户需求，选择最合适的语音和语速，以提高用户体验

4. **性能优化**：
   - 使用异步操作避免阻塞主线程
   - 对于需要多次合成的场景，可以复用 Communicate 对象

## 九、可用中文语音模型列表

"Multilingual" 标识：表示该语音可能支持多语言合成（如中英混合发音），但核心仍为中文语音。

| Name                                  | Gender    | VoicePersonalities                  |
|--------------------------------------|-----------|--------------------------------------|
| wuu-CN-XiaotongNeural                 | Female    | Warm, Friendly, Soothing             |
| wuu-CN-YunzheNeural                   | Male      | Calm, Deep, Gentle                   |
| yue-CN-XiaoMinNeural                  | Female    | Bright, Crisp, Confident             |
| yue-CN-YunSongNeural                  | Male      | Deep, Calm, Formal                   |
| zh-CN-XiaochenMultilingualNeural      | Female    | Friendly, Casual, Upbeat             |
| zh-CN-XiaochenNeural                  | Female    | Friendly, Casual, Upbeat             |
| zh-CN-XiaohanNeural                   | Female    | Gentle, Warm, Emotional              |
| zh-CN-XiaomengNeural                  | Female    | Gentle, Upbeat, Friendly             |
| zh-CN-XiaomoNeural                    | Female    | Deep, Casual, Calm                   |
| zh-CN-XiaoqiuNeural                   | Female    | Calm, Engaging, Soothing             |
| zh-CN-XiaorouNeural                   | Female    | Cheerful, Engaging, Pleasant         |
| zh-CN-XiaoruiNeural                   | Female    | Confident, Emotional, Hoarse         |
| zh-CN-XiaoshuangNeural                | Female    | Crisp, Cheerful, Bright              |
| zh-CN-XiaoxiaoDialectsNeural          | Female    | Warm, Animated, Bright               |
| zh-CN-XiaoxiaoMultilingualNeural      | Female    | Warm, Animated, Bright               |
| zh-CN-XiaoxiaoNeural                  | Female    | Warm, Well-Rounded, Animated         |
| zh-CN-XiaoyanNeural                   | Female    | Warm, Gentle, Empathetic             |
| zh-CN-XiaoyiNeural                    | Female    | Bright, Emotional, Engaging          |
| zh-CN-XiaoyouNeural                   | Female    | Crisp, Cheerful, Bright              |
| zh-CN-XiaoyuMultilingualNeural        | Female    | Deep, Confident, Casual              |
| zh-CN-XiaozhenNeural                  | Female    | Calm, Serious, Confident             |
| zh-CN-YunfengNeural                   | Male      | Confident, Animated, Emotional       |
| zh-CN-YunhaoNeural                    | Male      | Warm, Soft, Upbeat                   |
| zh-CN-YunjianNeural                   | Male      | Deep, Casual, Engaging               |
| zh-CN-YunjieNeural                    | Male      | Casual, Confident, Warm              |
| zh-CN-YunxiNeural                     | Male      | Bright, Animated, Cheerful           |
| zh-CN-YunxiaNeural                    | Male      | Cheerful, Friendly, Emotional        |
| zh-CN-YunxiaoMultilingualNeural       | Male      | Gentle, Casual, Friendly             |
| zh-CN-YunyangNeural                   | Male      | Formal, Deep, Calm                   |
| zh-CN-YunyeNeural                     | Male      | Casual, Deep, Calm                   |
| zh-CN-YunyiMultilingualNeural         | Male      | Gentle, Casual, Friendly             |
| zh-CN-YunzeNeural                     | Male      | Deep, Confident, Formal              |
| zh-CN-henan-YundengNeural             | Male      | Casual, Friendly, Animated           |
| zh-CN-liaoning-XiaobeiNeural          | Female    | Friendly, Casual, Gentle             |
| zh-CN-shaanxi-XiaoniNeural            | Female    | Confident, Engaging, Casual          |
| zh-CN-shandong-YunxiangNeural         | Male      | Casual, Animated, Strong             |
| zh-CN-sichuan-YunxiNeural             | Male      | Casual, Animated, Gentle             |
| zh-HK-HiuGaaiNeural                   | Female    | Crisp, Bright, Clear                 |
| zh-HK-HiuMaanNeural                   | Female    | Bright, Upbeat                       |
| zh-HK-WanLungNeural                   | Male      | Calm, Formal                         |
| zh-TW-HsiaoChenNeural                 | Female    | Soft, Caring                         |
| zh-TW-HsiaoYuNeural                   | Female    | Crisp, Bright, Clear                 |
| zh-TW-YunJheNeural                    | Male      | Engaging, Gentle                     |

## 十、常见问题

1. **服务启动后无法访问**
   - 检查Docker端口映射是否正确
   - 确认容器是否正在运行（使用`docker ps`命令）

2. **生成语音失败**
   - 检查网络连接是否正常（Edge-TTS需要连接Microsoft服务器）
   - 验证语音模型是否正确

3. **如何修改服务端口**
   - 修改app.py中的`app.run(host='0.0.0.0', port=5000, debug=True)`语句中的port参数
   - 同时更新Dockerfile中的`EXPOSE`指令和运行容器时的端口映射

4. **生成的音频文件没有声音**
   - 检查文本内容是否为空，或尝试调整音量参数

5. **语音合成失败或超时**
   - 检查网络连接，或尝试将长文本分成多个较短的部分

## 十一、注意事项

- 当前配置适用于开发环境，生产环境建议使用WSGI服务器如Gunicorn或uWSGI
- 生产环境应关闭debug模式
- 长时间运行可能需要考虑容器资源限制和自动重启策略
- 根据项目的 requirements.txt，当前版本要求 edge-tts>=6.1.4，并且支持 Python 3.9 或更高版本

## 十二、应用场景

- **在线教育平台**：将课程内容转换为语音，帮助学生更好地理解和记忆知识点
- **智能客服系统**：将自动生成的回复转换为语音，提供更加人性化的交互体验
- **无障碍应用**：为视觉障碍用户提供文本内容的语音朗读功能
- **内容创作工具**：为视频、动画等多媒体内容添加配音

---

文档更新时间：2024年7月