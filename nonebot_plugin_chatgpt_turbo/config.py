from pydantic import Extra, BaseModel
from typing import Optional


class Config(BaseModel, extra=Extra.ignore):
    oneapi_key: Optional[str] = ""  # （必填）OpenAI官方或者是支持OneAPI的大模型中转服务商提供的KEY
    oneapi_url: Optional[str] = ""  # （可选）大模型中转服务商提供的中转地址，使用OpenAI官方服务不需要填写
    oneapi_model: Optional[str] = "gpt-4o" # （可选）使用的语言大模型，使用识图功能请填写合适的大模型名称
    r1_reason: bool = True # （可选）使用DeepSeek-R1模型时是否展示思维链
    enable_private_chat: bool = True   # 是否开启私聊对话
    # chatgpt_turbo_public: bool = True  # 是否开启群聊对话

class ConfigError(Exception):
    pass

# 配置示例
# oneapi_key = "sk-xxx"  # OpenAI官方或者是支持OneAPI的大模型中转服务商提供的KEY
# oneapi_model = "deepseek-reasoner"
# oneapi_url = "https://api.deepseek.com"
# r1_reason = False
# enable_private_chat = True