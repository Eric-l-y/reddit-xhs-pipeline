"""LLM 翻译 + 小红书风格改编模块。支持任意 OpenAI 兼容 API。"""

import json
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)

# 内置预设：provider → (base_url, default_model)
PRESETS: dict[str, tuple[str, str]] = {
    "deepseek": ("https://api.deepseek.com/v1", "deepseek-chat"),
    "minimax": ("https://api.minimax.chat/v1", "MiniMax-Text-01"),
    "xiaomi": ("https://api.xiaomi.com/v1", "MiMo-7B"),
}

SYSTEM_PROMPT = """\
你是一个专业的内容编辑，擅长将英文 Reddit 帖子改编为小红书风格的中文内容。

要求：
1. 将英文内容翻译成地道的中文，不要直译，要意译
2. 语气要亲切、实用、有感染力，像朋友在分享经验
3. 根据内容性质选择合适的 emoji
4. 标题要吸引眼球，15-25 字，带 emoji
5. 正文用 bullet point 结构，每个要点用 emoji 开头
6. 生成 5-8 个相关的小红书话题标签（带 # 号）
7. 如果原文中有美国特有的文化背景，适当调整为更通用的表达

请严格按以下 JSON 格式输出，不要输出其他内容：
{
  "title": "带emoji的中文标题",
  "body": "结构化中文正文（含emoji bullet points）",
  "hashtags": ["#标签1", "#标签2", "#标签3"]
}"""


def resolve_provider(config: dict) -> tuple[str, str]:
    """根据配置解析出 base_url 和 model。

    Returns:
        (base_url, model) 元组
    """
    provider = config.get("provider", "deepseek")

    if provider == "custom":
        base_url = config.get("base_url")
        model = config.get("model")
        if not base_url or not model:
            raise ValueError("custom 模式必须填写 base_url 和 model")
        return base_url, model

    if provider not in PRESETS:
        available = ", ".join(PRESETS.keys())
        raise ValueError(f"未知 provider: {provider}，可用: {available}, custom")

    preset_url, preset_model = PRESETS[provider]
    # 允许用户覆盖 model
    model = config.get("model") or preset_model
    return preset_url, model


def create_client(api_key: str, base_url: str) -> OpenAI:
    """创建 OpenAI 兼容客户端。"""
    return OpenAI(api_key=api_key, base_url=base_url)


def translate_post(
    client: OpenAI,
    title: str,
    body: str,
    model: str,
    max_tokens: int = 4096,
) -> dict:
    """将 Reddit 帖子翻译并改编为小红书风格。

    Args:
        client: OpenAI 兼容客户端
        title: 原帖标题
        body: 原帖正文
        model: 模型名称
        max_tokens: 最大输出 token 数

    Returns:
        包含 title, body, hashtags 的字典
    """
    user_content = f"标题: {title}\n\n正文:\n{body}"

    logger.info(f"正在翻译: {title[:50]}...")

    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    print(f"DEBUG response type: {type(response)}, content: {response}")
text = response.choices[0].message.content

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取 JSON 块
        logger.warning("直接解析失败，尝试提取 JSON 块")
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(text[start:end])
        else:
            raise ValueError(f"无法从 LLM 响应中提取 JSON: {text[:200]}")

    logger.info(f"翻译完成: {result['title']}")
    return result
