"""小红书帖子排版和草稿输出模块。"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path

from src.models import RedditPost, XhsDraft

logger = logging.getLogger(__name__)


def format_draft(
    original_post: RedditPost,
    translated: dict,
    include_original: bool = True,
) -> XhsDraft:
    """组装小红书草稿。"""
    return XhsDraft(
        original_post=original_post,
        chinese_title=translated["title"],
        chinese_body=translated["body"],
        hashtags=translated["hashtags"],
    )


def _sanitize_filename(name: str, max_length: int = 50) -> str:
    """清理文件名，移除 Windows 非法字符。"""
    # 移除 Windows 非法字符
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    # 移除 emoji 和特殊 Unicode
    name = re.sub(r"[^\w\s一-鿿-]", "", name)
    # 压缩空格
    name = re.sub(r"\s+", "_", name.strip())
    return name[:max_length] if name else "untitled"


def save_markdown(draft: XhsDraft, output_dir: Path) -> Path:
    """将草稿保存为 Markdown 文件。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = draft.created_at.strftime("%Y%m%d_%H%M%S")
    title_slug = _sanitize_filename(draft.chinese_title)
    filename = f"{date_str}_{title_slug}.md"
    filepath = output_dir / filename

    hashtags_str = " ".join(draft.hashtags)

    content = f"""\
# {draft.chinese_title}

{draft.chinese_body}

{hashtags_str}

---

> **原始来源**: r/{draft.original_post.subreddit}
> **原帖分数**: {draft.original_post.score} | 评论: {draft.original_post.num_comments}
> **原文链接**: https://reddit.com{draft.original_post.permalink}
> **处理时间**: {draft.created_at.strftime("%Y-%m-%d %H:%M:%S")}

<details>
<summary>英文原文</summary>

### {draft.original_post.title}

{draft.original_post.selftext}

</details>
"""

    filepath.write_text(content, encoding="utf-8")
    logger.info(f"草稿已保存: {filepath}")
    return filepath


def save_json(draft: XhsDraft, output_dir: Path) -> Path:
    """将草稿保存为 JSON 文件。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = draft.created_at.strftime("%Y%m%d_%H%M%S")
    title_slug = _sanitize_filename(draft.chinese_title)
    filename = f"{date_str}_{title_slug}.json"
    filepath = output_dir / filename

    data = {
        "title": draft.chinese_title,
        "body": draft.chinese_body,
        "hashtags": draft.hashtags,
        "original": {
            "subreddit": draft.original_post.subreddit,
            "title": draft.original_post.title,
            "selftext": draft.original_post.selftext,
            "score": draft.original_post.score,
            "permalink": draft.original_post.permalink,
        },
        "created_at": draft.created_at.isoformat(),
    }

    filepath.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(f"草稿已保存: {filepath}")
    return filepath


def save_draft(draft: XhsDraft, output_dir: Path, fmt: str = "markdown") -> Path:
    """保存草稿（根据格式选择 markdown 或 json）。"""
    if fmt == "json":
        return save_json(draft, output_dir)
    return save_markdown(draft, output_dir)
