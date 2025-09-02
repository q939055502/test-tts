import os
import asyncio
import edge_tts
from datetime import datetime
# 导入日志配置
from logger_config import tts_logger, logger

class TTSService:
    def __init__(self):
        """初始化TTS服务"""
        # 确保输出目录存在
        self.output_dir = "output"
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
                tts_logger.info(f"创建输出目录: {self.output_dir}")
            except Exception as e:
                tts_logger.error(f"创建输出目录失败: {str(e)}")
                raise
        
        # 不再硬编码语音列表，而是通过list_available_voices方法动态获取
        
    def list_available_voices(self):
        """从Edge-TTS动态获取所有可用的语音模型
        
        返回:
            list: 语音模型名称列表
        """
        try:
            tts_logger.info("开始动态获取可用语音模型列表")
            # 异步获取语音列表
            voices = asyncio.run(edge_tts.list_voices())
            
            # 提取所有语音模型的ShortName
            available_voices = []
            for voice in voices:
                if 'ShortName' in voice:
                    voice_name = voice['ShortName']
                    available_voices.append(voice_name)
                    # 记录获取到的语音模型信息
                    tts_logger.debug(f"发现语音模型: {voice_name}")
            
            tts_logger.info(f"成功获取语音模型列表，共 {len(available_voices)} 个模型")
            return available_voices
        except Exception as e:
            error_msg = f"获取语音模型列表失败: {str(e)}"
            tts_logger.error(error_msg)
            # 发生异常时返回空列表
            return []
    
    def validate_voice(self, voice):
        """验证语音模型是否可用
        
        参数:
            voice (str): 语音模型名称
        
        返回:
            bool: 是否可用
        """
        try:
            available_voices = self.list_available_voices()
            result = voice in available_voices
            if not result:
                tts_logger.warning(f"验证语音模型: {voice} 不可用")
            else:
                tts_logger.debug(f"验证语音模型: {voice} 可用")
            return result
        except Exception as e:
            tts_logger.error(f"验证语音模型时出错: {str(e)}")
            return False
    
    async def generate_speech(self, text, voice="zh-CN-YunxiNeural", rate="+0%"):
        """异步生成语音文件
        
        参数:
            text (str): 要转换为语音的文本
            voice (str): 语音模型名称
            rate (str): 语速，格式为"+/-数字%"
        
        返回:
            dict: 生成结果，包含success、message、file_name、file_path等字段
        """
        try:
            # 生成唯一的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_name = f"tts_{timestamp}.mp3"
            file_path = os.path.join(self.output_dir, file_name)
            
            tts_logger.info(f"开始生成语音: 语音模型={voice}, 语速={rate}, 文本长度={len(text)}字符")
            
            # 创建TTS引擎
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            
            # 生成并保存语音文件
            with open(file_path, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
            
            tts_logger.info(f"语音生成成功: {file_name}, 保存路径: {file_path}")
            
            return {
                "success": True,
                "message": "语音生成成功",
                "file_name": file_name,
                "file_path": file_path
            }
        except Exception as e:
            error_msg = f"语音生成失败: {str(e)}"
            tts_logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
    
    def generate_speech_sync(self, text, voice="zh-CN-YunxiNeural", rate="+0%"):
        """同步生成语音文件
        
        参数:
            text (str): 要转换为语音的文本
            voice (str): 语音模型名称
            rate (str): 语速，格式为"+/-数字%"
        
        返回:
            dict: 生成结果，包含success、message、file_name、file_path等字段
        """
        try:
            tts_logger.info("调用同步语音生成方法")
            # 为每个线程创建一个新的事件循环（解决Flask多线程环境下的问题）
            try:
                # 尝试获取当前事件循环
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # 如果当前线程没有事件循环，则创建一个新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # 运行异步任务
            if loop.is_running():
                # 如果事件循环正在运行，使用create_task和run_coroutine_threadsafe
                future = asyncio.run_coroutine_threadsafe(self.generate_speech(text, voice, rate), loop)
                result = future.result()
            else:
                # 否则使用当前事件循环
                result = loop.run_until_complete(self.generate_speech(text, voice, rate))
                # 运行完成后关闭事件循环
                loop.close()
            return result
        except Exception as e:
            error_msg = f"同步语音生成失败: {str(e)}"
            tts_logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
    
    async def generate_speech_stream(self, text, voice="zh-CN-YunxiNeural", rate="+0%"):
        """异步生成流式语音
        
        参数:
            text (str): 要转换为语音的文本
            voice (str): 语音模型名称
            rate (str): 语速，格式为"+/-数字%"
        
        生成:
            bytes: 语音数据块
        """
        try:
            tts_logger.info(f"开始流式语音生成: 语音模型={voice}, 语速={rate}")
            
            # 创建TTS引擎
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            
            # 流式生成并返回语音数据
            chunk_count = 0
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunk_count += 1
                    yield chunk["data"]
            
            tts_logger.info(f"流式语音生成完成，共传输 {chunk_count} 个数据块")
        except Exception as e:
            error_msg = f"流式语音生成失败: {str(e)}"
            tts_logger.error(error_msg)
            # 尝试继续抛出异常，让上层处理
            raise Exception(error_msg)