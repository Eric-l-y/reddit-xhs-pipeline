"""Reddit 帖子抓取模块。通过 Arctic Shift API（Reddit 存档）抓取，无需 API Key，国内可访问。"""

import logging
import time
from datetime import datetime, timedelta

import requests

from src.models import RedditPost

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "xhs-pipeline:v1.0 (content research tool)"

# Arctic Shift API - Reddit 存档，数据更新更快
ARCTIC_SHIFT_URL = "https://arctic-shift.photon-reddit.com/api/posts/search"

# 每次最多拉 100 条，然后本地按分数排序筛选
BATCH_SIZE = 100


def fetch_posts(
    subreddit_name: str,
    sort: str = "top",
    time_filter: str = "week",
    limit: int = 20,
    user_agent: str = DEFAULT_USER_AGENT,
) -> list[RedditPost]:
    """通过 Arctic Shift API 抓取 Reddit 帖子。

    Arctic Shift 是 Reddit 的公开存档，数据更新比 Pullpush 更快，
    国内可直接访问。

    Args:
        subreddit_name: 子版块名称
        sort: 排序方式 (top/hot/new/rising)
        time_filter: 时间过滤 (hour/day/week/month/year/all)
        limit: 返回数量上限
        user_agent: 请求的 User-Agent
    """
    logger.info(f"正在抓取 r/{subreddit_name} (limit={limit})")

    # 计算时间范围
    time_map = {
        "hour": 3600,
        "day": 86400,
        "week": 604800,
        "month": 2592000,
        "year": 31536000,
        "all": 0,
    }
    after_ts = int(time.time()) - time_map.get(time_filter, 604800)

    headers = {"User-Agent": user_agent}
    params = {
        "subreddit": subreddit_name,
        "limit": BATCH_SIZE,
        "sort": "desc",
        "sort_type": "created_utc",
        "after": after_ts,
        "fields": "id,title,score,created_utc,selftext,num_comments",
    }

    try:
        resp = requests.get(
            ARCTIC_SHIFT_URL, params=params, headers=headers, timeout=30
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"请求失败: {e}")
        return []

    data = resp.json().get("data", [])
    logger.info(f"从 Arctic Shift 获取到 {len(data)} 条原始数据")

    # 转换为 RedditPost 并按分数排序
    posts = []
    for d in data:
        # 跳过已删除/已移除的帖子
        selftext = d.get("selftext", "")
        if selftext in ("[deleted]", "[removed]", ""):
            continue

        # 构建 permalink（Arctic Shift 不返回此字段）
        post_id = d.get("id", "")
        permalink = f"/r/{subreddit_name}/comments/{post_id}/"

        post = RedditPost(
            id=post_id,
            subreddit=subreddit_name,
            title=d.get("title", ""),
            selftext=selftext,
            score=d.get("score", 0),
            upvote_ratio=0.95,  # Arctic Shift 不提供此字段，设默认值
            num_comments=d.get("num_comments", 0),
            url=f"https://reddit.com{permalink}",
            permalink=permalink,
            created_utc=d.get("created_utc", 0.0),
            is_nsfw=False,
            is_stickied=False,
        )
        posts.append(post)

    # 按分数降序排列
    posts.sort(key=lambda p: p.score, reverse=True)

    # 取前 limit 条
    posts = posts[:limit]
    logger.info(f"从 r/{subreddit_name} 筛选出 {len(posts)} 个高质量帖子")
    return posts
