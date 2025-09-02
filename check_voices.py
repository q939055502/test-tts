import asyncio
import edge_tts
import json

async def get_available_voices():
    try:
        # 获取所有可用语音
        voices = await edge_tts.list_voices()
        
        # 提取所有包含'Neural'的中文语音
        chinese_neural_voices = []
        for voice in voices:
            if 'zh' in voice.get('ShortName', '') and 'Neural' in voice.get('ShortName', ''):
                chinese_neural_voices.append(voice.get('ShortName'))
        
        print("=== 容器内可用的中文Neural语音模型 ===")
        print(json.dumps(chinese_neural_voices, ensure_ascii=False, indent=2))
        print(f"\n总共有 {len(chinese_neural_voices)} 个可用的中文Neural语音模型")
        
        # 特别检查zh-CN-YunxiNeural是否存在
        if 'zh-CN-YunxiNeural' in chinese_neural_voices:
            print("\n✓ zh-CN-YunxiNeural 语音模型可用")
        else:
            print("\n✗ zh-CN-YunxiNeural 语音模型不可用")
            print("\n请使用以下可用的语音模型之一：")
            for voice in chinese_neural_voices:
                print(f"- {voice}")
                
    except Exception as e:
        print(f"获取语音列表失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(get_available_voices())