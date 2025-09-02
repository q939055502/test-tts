from flask import Flask, request, jsonify, send_file, abort
import os
from tts_service import TTSService
from flask import Response
import asyncio
from functools import wraps
# 导入日志配置
from logger_config import logger, access_logger, tts_logger

app = Flask(__name__)
# 初始化TTS服务
tts_service = TTSService()

# 安全配置
# 从环境变量读取配置，如果环境变量不存在则使用默认值
# API密钥 - 可以使用generate_api_key()生成一个新的密钥
API_KEY = os.environ.get("API_KEY", "4b7c9e2a-3d8f-5a1b-6c4d-7e8f9a0b1c2d")  # 示例密钥，请在生产环境中更换
# IP白名单 - 限制只有指定的IP可以访问API
# 环境变量格式：逗号分隔的IP列表，如"192.168.1.100,127.0.0.1"
allowed_ips_str = os.environ.get("ALLOWED_IPS", "")
ALLOWED_IPS = [ip.strip() for ip in allowed_ips_str.split(",")] if allowed_ips_str else []

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
    # 允许访问首页和健康检查接口
    if request.path in ['/', '/api/health']:
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
def home():
    """首页接口"""
    logger.info("访问首页")
    return jsonify({
        "message": "欢迎使用Edge-TTS API服务",
        "version": "1.0",
        "endpoints": [
            "/api/tts - 生成语音",
            "/api/voices - 获取可用语音列表",
            "/api/health - 健康检查"
        ]
    })


@app.route('/api/health')
def health_check():
    """健康检查接口"""
    logger.info("健康检查请求")
    return jsonify({
        "status": "healthy",
        "message": "服务运行正常"
    })


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
            # 检查是否需要直接返回文件
            return_json = request.args.get('return_json', 'false').lower() == 'true'
            logger.info(f"语音生成成功: {result['file_name']}")
            
            if return_json:
                # 返回JSON结果
                return jsonify({
                    "success": True,
                    "message": "语音生成成功",
                    "file_name": result['file_name'],
                    "voice": voice,
                    "rate": rate,
                    "file_path": result['file_path']
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


if __name__ == "__main__":
    # 在开发环境中运行Flask应用
    # 注意：生产环境中应使用WSGI服务器如Gunicorn或uWSGI
    logger.info("启动Edge-TTS API服务")
    logger.info(f"服务监听地址: http://0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)