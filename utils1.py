#生成秘钥
import uuid
import secrets
import string


def generate_strong_key(length=32, use_symbols=True):
    """生成一个强加密密钥
    
    参数:
        length (int): 密钥长度，默认为32
        use_symbols (bool): 是否包含特殊字符，默认为True
    
    返回:
        str: 生成的强密钥
    """
    # 定义字符集
    characters = string.ascii_letters + string.digits
    
    # 如果需要特殊字符，添加特殊字符集
    if use_symbols:
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        characters += symbols
    
    # 使用secrets模块生成密码安全的随机密钥
    key = ''.join(secrets.choice(characters) for _ in range(length))
    return key


def generate_api_key():
    """生成一个基于UUID的API密钥
    
    返回:
        str: 格式化的API密钥
    """
    # 生成一个UUID4，并格式化为更易读的形式
    api_key = str(uuid.uuid4()).replace('-', '')
    # 按每8个字符一组格式化，提高可读性
    return '-'.join([api_key[i:i+8] for i in range(0, len(api_key), 8)])


if __name__ == "__main__":
    """测试密钥生成函数"""
    print("=== 测试强密码生成函数 ===")
    
    # 测试默认参数（32位，包含特殊字符）
    print("\n1. 默认32位强密钥（包含特殊字符）:")
    default_key = generate_strong_key()
    print(f"密钥: {default_key}")
    print(f"长度: {len(default_key)}")
    
    # 测试自定义长度
    print("\n2. 自定义16位强密钥:")
    short_key = generate_strong_key(length=16)
    print(f"密钥: {short_key}")
    print(f"长度: {len(short_key)}")
    
    # 测试不包含特殊字符
    print("\n3. 不包含特殊字符的密钥:")
    no_symbols_key = generate_strong_key(use_symbols=False)
    print(f"密钥: {no_symbols_key}")
    print(f"包含特殊字符? {'否' if all(c.isalnum() for c in no_symbols_key) else '是'}")
    
    # 测试API密钥生成
    print("\n=== 测试API密钥生成函数 ===")
    api_key = generate_api_key()
    print(f"API密钥: {api_key}")
    print(f"格式: 8字符一组，共{len(api_key.split('-'))}组")

