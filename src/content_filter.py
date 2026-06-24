"""内容质量过滤和去重模块。"""

import json
import logging
from pathlib import Path

from src.models import RedditPost

logger = logging.getLogger(__name__)

SEEN_POSTS_FILE = Path("data/seen_posts.json")


def load_seen_post_ids() -> set[str]:
    """加载已处理过的帖子 ID 集合。"""
    if not SEEN_POSTS_FILE.exists():
        return set()
    try:
        data = json.loads(SEEN_POSTS_FILE.read_text(encoding="utf-8"))
        return set(data)
    except (json.JSONDecodeError, TypeError):
        logger.warning("seen_posts.json 格式异常，重置为空")
        return set()


def save_seen_post_ids(seen_ids: set[str]) -> None:
    """保存已处理的帖子 ID。"""
    SEEN_POSTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_POSTS_FILE.write_text(
        json.dumps(list(seen_ids), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def filter_posts(
    posts: list[RedditPost],
    seen_ids: set[str],
    min_score: int = 500,
    min_upvote_ratio: float = 0.85,
    exclude_nsfw: bool = True,
    exclude_stickied: bool = True,
    min_text_length: int = 100,
) -> list[RedditPost]:
    """过滤低质量帖子和已处理过的帖子。

    Args:
        posts: 待过滤的帖子列表
        seen_ids: 已处理过的帖子 ID 集合
        min_score: 最低分数阈值
        min_upvote_ratio: 最低好评率
        exclude_nsfw: 是否排除 NSFW 内容
        exclude_stickied: 是否排除置顶帖
        min_text_length: 正文最短长度
    """
    filtered = []
    for post in posts:
        # 去重
        if post.id in seen_ids:
            logger.debug(f"跳过已处理: {post.id}")
            continue

        # NSFW 过滤
        if exclude_nsfw and post.is_nsfw:
            logger.debug(f"跳过 NSFW: {post.id}")
            continue

        # 置顶帖过滤
        if exclude_stickied and post.is_stickied:
            logger.debug(f"跳过置顶帖: {post.id}")
            continue

        # 分数过滤
        if post.score < min_score:
            logger.debug(f"跳过低分 ({post.score}): {post.id}")
            continue

        # 好评率过滤
        if post.upvote_ratio < min_upvote_ratio:
            logger.debug(f"跳过低好评率 ({post.upvote_ratio}): {post.id}")
            continue

        # 文本长度过滤（跳过纯链接帖）
        if len(post.selftext.strip()) < min_text_length:
            logger.debug(f"跳过短文本 ({len(post.selftext)}): {post.id}")
            continue

        filtered.append(post)

    logger.info(
        f"过滤完成: {len(posts)} → {len(filtered)} "
        f"(去重/NSFW/置顶/低分/短文本 已排除)"
    )
    return filtered
