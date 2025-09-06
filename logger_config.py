import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
# 创建日志目录
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件路径
LOG_FILE = os.path.join(LOG_DIR, 'tts_service.log')
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'tts_service_error.log')

# 配置基本日志格式
LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def custom_time(*args):
    return datetime.now(timezone.utc).astimezone().timetuple()
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
formatter.converter = custom_time  # 强制使用本地时区

# 创建logger
def setup_logger(name=__name__, log_level=logging.INFO):
    """设置日志记录器
    
    参数:
        name (str): 日志记录器名称
        log_level (int): 日志级别
        
    返回:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 避免重复添加处理器
    if not logger.handlers:
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # 创建文件处理器（普通日志）
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,          # 保留5个备份文件
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # 创建错误日志处理器
        error_file_handler = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,          # 保留5个备份文件
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        
        # 创建格式化器
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        
        # 设置处理器的格式化器
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        error_file_handler.setFormatter(formatter)
        
        # 添加处理器到日志记录器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.addHandler(error_file_handler)
    
    return logger

# 创建默认的logger实例
logger = setup_logger()

# 应用访问日志记录器
access_logger = setup_logger('access', logging.INFO)

# TTS服务日志记录器
tts_logger = setup_logger('tts', logging.INFO)