from flask import Flask, request, jsonify, send_file, abort, render_template, send_from_directory
import os
from tts_service import TTSService
from flask import Response
import asyncio
from functools import wraps
# 导入日志配置
from logger_config import logger, access_logger, tts_logger

# 尝试导入并配置CORS
try:
    from flask_cors import CORS
    CORS_INSTALLED = True
except ImportError:
    CORS_INSTALLED = False

app = Flask(__name__)
# 初始化TTS服务
tts_service = TTSService()

# 如果安装了flask_cors，则配置CORS
if CORS_INSTALLED:
    CORS(app, origins="*")
    logger.info("已启用CORS支持")
# 安全配置
# 从环境变量读取配置，如果环境变量不存在则使用默认值
# API密钥 - 可以使用generate_api_key()生成一个新的密钥
API_KEY = os.environ.get("API_KEY", "4b7c9e2a-3d8f-5a1b-6c4d-7e8f9a0b1c2d")  # 示例密钥，请在生产环境中更换
# IP白名单 - 限制只有指定的IP可以访问API
# 环境变量格式：逗号分隔的IP列表，如"192.168.1.100,127.0.0.1"
allowed_ips_str = os.environ.get("ALLOWED_IPS", "")
ALLOWED_IPS = [ip.strip() for ip in allowed_ips_str.split(",")] if allowed_ips_str else []

# 配置文件上传目录
UPLOAD_FOLDER = 'output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 确保上传目录存在
if not os.path.exists(UPLOAD_FOLDER):
    try:
        os.makedirs(UPLOAD_FOLDER)
        logger.info(f"创建上传目录: {UPLOAD_FOLDER}")
    except Exception as e:
        logger.error(f"创建上传目录失败: {str(e)}")

# 将异步函数转换为同步函数的装饰器
def async_to_sync(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return decorated_function

# 请求日志记录中间件
def log_request_middleware():
    """记录请求信息的中间件"""
    # 记录请求信息
    client_ip = request.remote_addr
    method = request.method
    path = request.path
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # 记录访问日志
    access_logger.info(f"请求: IP={client_ip}, 方法={method}, 路径={path}, UA={user_agent}")

# 身份验证中间件
def auth_middleware():
    """身份验证中间件，用于保护敏感接口"""
    # 允许访问首页、健康检查接口、必要的静态资源和生成的音频文件
    if request.path in ['/','/api/voice_list', '/api/voice_sample', '/favicon.ico'] or request.path.startswith('/static/audio/'):
        return
    
    # IP白名单验证
    if ALLOWED_IPS:
        client_ip = request.remote_addr
        if client_ip not in ALLOWED_IPS:
            logger.warning(f"IP未授权: {client_ip} 尝试访问 {request.path}")
            abort(403, description="IP未授权")
    
    # API密钥验证 - 同时支持从请求头和查询参数中读取
    api_key = request.headers.get("X-API-Key") or request.args.get("X-API-Key")
    if not api_key:
        logger.warning(f"API密钥缺失: {request.remote_addr} 访问 {request.path}")
        abort(401, description="API密钥错误")
    elif api_key != API_KEY:
        logger.warning(f"API密钥错误: {request.remote_addr} 使用无效密钥访问 {request.path}")
        abort(401, description="API密钥错误")

# 静态文件路由 - 允许访问output目录中的音频文件
@app.route('/static/audio/<filename>')
def serve_audio(filename):
    """提供音频文件的静态访问"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, mimetype='audio/mpeg')
    except FileNotFoundError:
        abort(404)

# 注册中间件
app.before_request(log_request_middleware)
app.before_request(auth_middleware)

# 错误处理
@app.errorhandler(401)
def unauthorized(error):
    logger.warning(f"401错误: {error.description}")
    return jsonify({
        "success": False,
        "error": "Unauthorized",
        "message": error.description
    }), 401

@app.errorhandler(403)
def forbidden(error):
    logger.warning(f"403错误: {error.description}")
    return jsonify({
        "success": False,
        "error": "Forbidden",
        "message": error.description
    }), 403

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404错误: 路径 {request.path} 不存在")
    return jsonify({
        "success": False,
        "error": "Not Found",
        "message": "请求的资源不存在"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    logger.warning(f"405错误: {request.method} 方法不允许访问 {request.path}")
    return jsonify({
        "success": False,
        "error": "Method Not Allowed",
        "message": "不允许的请求方法"
    }), 405

@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"500错误: {str(error)}")
    return jsonify({
        "success": False,
        "error": "Internal Server Error",
        "message": "服务器内部错误"
    }), 500


@app.route('/')
def voice_demo():
    """语音试听页面"""
    logger.info("访问语音试听页面")
    return render_template('voice_demo.html')


@app.route('/api/voices', methods=['GET'])
def get_voices():
    """获取可用语音列表接口
    
    返回:
        JSON: 可用的中文语音模型列表
    """
    try:
        logger.info(f"获取语音列表请求")
        voices = tts_service.list_available_voices()
        logger.info(f"成功获取语音列表，共 {len(voices)} 个语音模型")
        return jsonify({
            "success": True,
            "voices": voices,
            "count": len(voices)
        })
    except Exception as e:
        logger.error(f"获取语音列表失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取语音列表失败: {str(e)}"
        }), 500


@app.route('/api/tts', methods=['POST'])
def generate_tts():
    """生成语音接口
    
    请求体参数:
        text (str): 要转换为语音的文本（必需）
        voice (str): 语音模型（可选，默认为zh-CN-YunxiNeural）
        rate (str): 语速（可选，默认为+0%）
    
    返回:
        JSON: 生成结果信息或直接返回语音文件
    """
    try:
        # 获取请求参数
        data = request.get_json()
        
        # 验证必需参数
        if not data or 'text' not in data:
            logger.warning("语音生成请求缺少必需参数: text")
            return jsonify({
                "success": False,
                "message": "缺少必需参数: text"
            }), 400
        
        # 获取参数值，设置默认值
        text = data['text']
        voice = data.get('voice', 'zh-CN-YunxiNeural')
        rate = data.get('rate', '+0%')
        
        # 记录请求信息（注意：不记录完整文本内容，防止敏感信息泄露）
        logger.info(f"语音生成请求: 语音模型={voice}, 语速={rate}, 文本长度={len(text)}字符")
        
        # 验证文本长度
        if len(text.strip()) == 0:
            logger.warning("语音生成请求文本为空")
            return jsonify({
                "success": False,
                "message": "文本不能为空"
            }), 400
        
        # 验证语音模型
        if not tts_service.validate_voice(voice):
            logger.warning(f"语音生成请求: 不支持的语音模型: {voice}")
            return jsonify({
                "success": False,
                "message": f"不支持的语音模型: {voice}",
                "available_voices": tts_service.list_available_voices()
            }), 400
        
        # 生成语音
        result = tts_service.generate_speech_sync(text, voice, rate)
        
        if result['success']:
            # 检查是否需要直接返回文件 - 同时支持从查询参数和请求体中获取
            return_json = request.args.get('return_json', 'false').lower() == 'true' or data.get('return_json', False)
            logger.info(f"语音生成成功: {result['file_name']}")
            
            if return_json:
                # 返回JSON结果，包含可访问的文件URL
                file_url = f"{request.host_url}static/audio/{result['file_name']}"
                return jsonify({
                    "success": True,
                    "message": "语音生成成功",
                    "file_name": result['file_name'],
                    "voice": voice,
                    "rate": rate,
                    "file_path": result['file_path'],
                    "file_url": file_url
                })
            else:
                # 直接返回语音文件
                return send_file(
                    result['file_path'],
                    mimetype='audio/mpeg',
                    as_attachment=True,
                    download_name=result['file_name']
                )
        else:
            logger.error(f"语音生成失败: {result['message']}")
            return jsonify({
                "success": False,
                "message": result['message']
            }), 500
    except Exception as e:
        logger.error(f"处理语音生成请求时发生错误: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"处理请求时发生错误: {str(e)}"
        }), 500

@app.route('/api/tts/stream', methods=['POST'])
def generate_tts_stream():
    """生成流式语音接口
    
    请求体参数:
        text (str): 要转换为语音的文本（必需）
        voice (str): 语音模型（可选，默认为zh-CN-YunxiNeural）
        rate (str): 语速（可选，默认为+0%）
    
    返回:
        流式音频数据
    """
    try:
        # 获取请求参数
        data = request.get_json()
        
        # 验证必需参数
        if not data or 'text' not in data:
            logger.warning("流式语音生成请求缺少必需参数: text")
            return jsonify({
                "success": False,
                "message": "缺少必需参数: text"
            }), 400
        
        # 获取参数值，设置默认值
        text = data['text']
        voice = data.get('voice', 'zh-CN-YunxiNeural')
        rate = data.get('rate', '+0%')
        
        # 记录请求信息（注意：不记录完整文本内容，防止敏感信息泄露）
        logger.info(f"流式语音生成请求: 语音模型={voice}, 语速={rate}, 文本长度={len(text)}字符")
        
        # 验证文本长度
        if len(text.strip()) == 0:
            logger.warning("流式语音生成请求文本为空")
            return jsonify({
                "success": False,
                "message": "文本不能为空"
            }), 400
        
        # 验证语音模型
        if not tts_service.validate_voice(voice):
            logger.warning(f"流式语音生成请求: 不支持的语音模型: {voice}")
            return jsonify({
                "success": False,
                "message": f"不支持的语音模型: {voice}",
                "available_voices": tts_service.list_available_voices()
            }), 400
        
        # 定义流式响应生成器函数
        @async_to_sync
        async def audio_stream():
            try:
                async for chunk in tts_service.generate_speech_stream(text, voice, rate):
                    yield chunk
            except Exception as e:
                logger.error(f"流式语音响应错误: {str(e)}")
        
        # 返回流式响应
        logger.info(f"开始流式语音传输: 语音模型={voice}")
        return Response(audio_stream(), mimetype='audio/mpeg')
    except Exception as e:
        logger.error(f"处理流式语音生成请求时发生错误: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"处理请求时发生错误: {str(e)}"
        }), 500


@app.route('/api/voice_list')
def get_voice_list():
    """获取语音列表接口
    
    返回:
        JSON: 从voice_list.txt文件中读取的语音列表
    """
    try:
        # 使用相对路径，确保在容器内也能正确读取文件
        voice_list_path = 'voice_list.txt'
        # 如果相对路径不存在，尝试使用环境变量或备用路径
        if not os.path.exists(voice_list_path):
            # 检查是否有环境变量设置的路径
            voice_list_path = os.environ.get('VOICE_LIST_PATH', 'voice_list.txt')
            
            if not os.path.exists(voice_list_path):
                logger.error(f"语音列表文件不存在: {voice_list_path}")
                # 返回预设的示例语音列表，确保前端页面能够正常显示
                sample_voices = [
                    'zh-CN-XiaomoNeural', 'zh-CN-XiaoxueNeural', 
                    'zh-CN-XiaorouNeural', 'zh-CN-YunxiNeural',
                    'en-US-JennyNeural', 'en-US-BrianNeural'
                ]
                return jsonify(sample_voices)
        
        with open(voice_list_path, 'r', encoding='utf-8') as f:
            voices = [line.strip() for line in f if line.strip()]
        
        logger.info(f"成功读取语音列表，共 {len(voices)} 个语音模型")
        return jsonify(voices)
    except Exception as e:
        logger.error(f"读取语音列表失败: {str(e)}")
        return jsonify([]), 500

@app.route('/api/voice_sample')
def get_voice_sample():
    """获取语音样本接口
    
    参数:
        voice (str): 语音模型名称
    
    返回:
        audio/mpeg: 语音样本文件
    """
    try:
        # 获取语音模型参数
        voice = request.args.get('voice')
        if not voice:
            logger.warning("语音样本请求缺少voice参数")
            abort(400, description="缺少voice参数")
        
        # 定义一个示例文本用于生成语音样本
        sample_text = "这是一个语音样本，用于测试Edge-TTS的声音效果。"
        
        # 检查是否是中文语音，使用不同的示例文本
        if voice.startswith('zh-'):
            sample_text = "这是一个语音样本，用于测试Edge-TTS的声音效果。"
        elif voice.startswith('en-'):
            sample_text = "This is a voice sample for testing Edge-TTS sound effects."
        else:
            # 对于其他语言，使用英文作为默认
            sample_text = "This is a voice sample for testing Edge-TTS sound effects."
        
        logger.info(f"生成语音样本请求: 语音模型={voice}")
        
        # 使用tts_service生成语音样本
        result = tts_service.generate_speech_sync(sample_text, voice)
        
        if result['success']:
            logger.info(f"语音样本生成成功: {result['file_name']}")
            # 直接返回语音文件
            return send_file(
                result['file_path'],
                mimetype='audio/mpeg',
                as_attachment=False
            )
        else:
            logger.error(f"语音样本生成失败: {result['message']}")
            abort(500, description=f"生成语音样本失败: {result['message']}")
    except Exception as e:
        logger.error(f"处理语音样本请求时发生错误: {str(e)}")
        abort(500, description=f"处理请求时发生错误: {str(e)}")

@app.route('/api/tts/batch', methods=['POST'])
def generate_tts_batch():
    """批量生成语音接口
    
    请求体参数:
        Array: 包含多个语音生成任务的数组，每个任务包含：
            text (str): 要转换为语音的文本（必需）
            voice (str): 语音模型（可选，默认为zh-CN-YunxiNeural）
            rate (str): 语速（可选，默认为+0%）
    
    返回:
        JSON: 包含所有生成任务结果的数组，每个结果包含link和msg字段
    """
    try:
        # 获取请求参数
        data = request.get_json()
        
        # 验证必需参数
        if not data or not isinstance(data, list):
            logger.warning("批量语音生成请求参数不是有效的数组")
            return jsonify({
                "code": 400,
                "data": [],
                "msg": "请求参数必须是有效的数组"
            })
        
        # 记录请求信息
        logger.info(f"批量语音生成请求: 共 {len(data)} 个任务")
        
        # 处理每个语音生成任务
        results = []
        for i, task in enumerate(data):
            try:
                # 验证任务必需参数
                if not task or 'text' not in task:
                    logger.warning(f"批量任务 {i+1} 缺少必需参数: text")
                    results.append({
                        "code": 400,
                        "data": None,
                        "msg": "缺少必需参数: text"
                    })
                    continue
                
                # 获取任务参数值，设置默认值
                text = task['text']
                voice = task.get('voice', 'zh-CN-YunxiNeural')
                rate = task.get('rate', '+0%')
                
                # 验证文本长度
                if len(text.strip()) == 0:
                    logger.warning(f"批量任务 {i+1} 文本为空")
                    results.append({
                        "code": 400,
                        "data": None,
                        "msg": "文本不能为空"
                    })
                    continue
                
                # 验证语音模型
                if not tts_service.validate_voice(voice):
                    logger.warning(f"批量任务 {i+1} 不支持的语音模型: {voice}")
                    results.append({
                        "code": 400,
                        "data": None,
                        "msg": f"不支持的语音模型: {voice}"
                    })
                    continue
                
                # 生成语音
                result = tts_service.generate_speech_sync(text, voice, rate)
                
                if result['success']:
                    logger.info(f"批量任务 {i+1} 语音生成成功: {result['file_name']}")
                    # 生成文件URL
                    file_url = f"{request.host_url}static/audio/{result['file_name']}"
                    results.append({
                        "code": 0,
                        "data": {
                            "link": file_url
                        },
                        "msg": "success"
                    })
                else:
                    logger.error(f"批量任务 {i+1} 语音生成失败: {result['message']}")
                    results.append({
                        "code": 500,
                        "data": None,
                        "msg": result['message']
                    })
            except Exception as e:
                logger.error(f"处理批量任务 {i+1} 时发生错误: {str(e)}")
                results.append({
                    "code": 500,
                    "data": None,
                    "msg": f"处理请求时发生错误: {str(e)}"
                })
        
        # 返回所有任务的结果
        return jsonify(results)
    except Exception as e:
        logger.error(f"处理批量语音生成请求时发生错误: {str(e)}")
        return jsonify({
            "code": 500,
            "data": [],
            "msg": f"处理请求时发生错误: {str(e)}"
        })


if __name__ == "__main__":
    # 在开发环境中运行Flask应用
    # 注意：生产环境中应使用WSGI服务器如Gunicorn或uWSGI
    logger.info("启动Edge-TTS API服务")
    logger.info(f"服务监听地址: http://0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)