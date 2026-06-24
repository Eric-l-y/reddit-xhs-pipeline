"""数据模型定义。"""

from datetime import datetime

from pydantic import BaseModel, Field


class RedditPost(BaseModel):
    """Reddit 帖子数据模型。"""

    id: str
    subreddit: str
    title: str
    selftext: str
    score: int
    upvote_ratio: float
    num_comments: int
    url: str
    permalink: str
    created_utc: float
    is_nsfw: bool
    is_stickied: bool


class XhsDraft(BaseModel):
    """小红书草稿数据模型。"""

    original_post: RedditPost
    chinese_title: str = Field(description="带 emoji 的中文标题")
    chinese_body: str = Field(description="结构化中文正文")
    hashtags: list[str] = Field(description="小红书话题标签")
    created_at: datetime = Field(default_factory=datetime.now)
