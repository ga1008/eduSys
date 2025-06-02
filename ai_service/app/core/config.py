import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings  # pydantic v2
from typing import Optional

# 项目根目录的 .env 文件
# 注意：这里的路径假设 ai_service 是 eduSys 的子目录
# 如果 ai_service 独立于 eduSys 目录，则需要调整 BASE_DIR 的计算
# 或者确保 .env 文件在 ai_service 启动的当前工作目录下
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, '.env'))


# print(f"Loading .env from: {os.path.join(BASE_DIR, '.env')}") # 用于调试

class Settings(BaseSettings):
    # DeepSeek
    DS_API_KEY: str
    DS_BASE_URL: str = "https://api.deepseek.com"
    DS_MODEL: str = "deepseek-chat"
    DS_MODEL_R: str = "deepseek-coder"  # 或其他推理模型

    # SiliconFlow
    SF_API_KEY: str
    SF_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SF_MODEL: str = "deepseek-ai/DeepSeek-V2"
    SF_MODEL_R: str = "deepseek-ai/DeepSeek-V2"

    # VolcEngine (ARK)
    VC_API_KEY: str
    VC_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    VC_MODEL: str = "ark_deepseek-v2-lite-240619"  # 示例模型，请按实际情况修改
    VC_MODEL_R: str = "ark_deepseek-v2-chat-240619"  # 示例模型

    ARK_API_KEY: Optional[str] = None  # 从VC_API_KEY继承

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # AI Router
    DEFAULT_TIMEOUT: int = 120  # 默认超时时间（秒）
    RETRY_ATTEMPTS: int = 2  # 默认重试次数

    class Config:
        env_file = os.path.join(BASE_DIR, '.env')
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # 忽略.env中多余的变量


settings = Settings()
# 确保火山引擎的 API Key 也设置到环境变量，因为其SDK默认从环境变量读取
if settings.VC_API_KEY and not os.getenv("ARK_API_KEY"):
    os.environ["ARK_API_KEY"] = settings.VC_API_KEY
