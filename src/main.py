"""Reddit → 小红书 内容管道 CLI 入口。"""

import argparse
import logging
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.content_filter import filter_posts, load_seen_post_ids, save_seen_post_ids
from src.formatter import format_draft, save_draft
from src.reddit_scraper import fetch_posts
from src.translator import create_client, resolve_provider, translate_post

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """加载 YAML 配置文件。"""
    path = Path(config_path)
    if not path.exists():
        logger.error(f"配置文件不存在: {config_path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Reddit 热门帖子 → 小红书草稿 内容管道"
    )
    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="配置文件路径 (默认: config/settings.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只抓取和过滤，不调用 LLM 翻译",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="每个 subreddit 最多处理的帖子数（覆盖配置文件）",
    )
    args = parser.parse_args()

    # 加载环境变量和配置
    load_dotenv()
    config = load_config(args.config)

    # 翻译配置
    trans_config = config["translation"]
    api_key_env = trans_config.get("api_key_env", "LLM_API_KEY")

    # 解析 LLM provider → base_url + model
    base_url, model = resolve_provider(trans_config)
    logger.info(f"LLM: {trans_config.get('provider')} | 模型: {model} | API: {base_url}")

    # 初始化 LLM 客户端
    if not args.dry_run:
        api_key = os.getenv(api_key_env)
        if not api_key:
            logger.error(f"缺少环境变量: {api_key_env}")
            logger.error("请在 .env 文件中设置你的 LLM API Key")
            sys.exit(1)
        llm_client = create_client(api_key=api_key, base_url=base_url)

    # 输出目录
    output_dir = Path(config["output"]["directory"])
    output_fmt = config["output"].get("format", "markdown")
    include_original = config["output"].get("include_original", True)

    # 加载已处理的帖子 ID
    seen_ids = load_seen_post_ids()
    logger.info(f"已记录 {len(seen_ids)} 个已处理帖子")

    # 处理每个 subreddit
    all_drafts = []
    total_fetched = 0
    total_filtered = 0
    total_translated = 0

    for sub_config in config["reddit"]["subreddits"]:
        sub_name = sub_config["name"]
        sort = sub_config.get("sort", "top")
        time_filter = sub_config.get("time_filter", "week")
        limit = args.limit or sub_config.get("limit", 20)

        # 抓取
        posts = fetch_posts(
            subreddit_name=sub_name,
            sort=sort,
            time_filter=time_filter,
            limit=limit,
        )
        total_fetched += len(posts)

        # 过滤
        filtered = filter_posts(
            posts,
            seen_ids,
            min_score=config["reddit"].get("min_score", 500),
            min_upvote_ratio=config["reddit"].get("min_upvote_ratio", 0.85),
            exclude_nsfw=config["reddit"].get("exclude_nsfw", True),
            exclude_stickied=config["reddit"].get("exclude_stickied", True),
            min_text_length=config["reddit"].get("min_text_length", 100),
        )
        total_filtered += len(filtered)

        if args.dry_run:
            logger.info(f"[DRY RUN] r/{sub_name}: {len(filtered)} 个帖子通过过滤")
            for post in filtered:
                logger.info(f"  - [{post.score}分] {post.title[:60]}")
            continue

        # 翻译 + 格式化
        for post in filtered:
            try:
                translated = translate_post(
                    llm_client,
                    title=post.title,
                    body=post.selftext,
                    model=model,
                    max_tokens=trans_config.get("max_tokens", 4096),
                )

                draft = format_draft(post, translated, include_original)
                saved_path = save_draft(draft, output_dir, output_fmt)

                all_drafts.append(draft)
                seen_ids.add(post.id)
                total_translated += 1

                logger.info(f"✅ 已生成草稿: {draft.chinese_title}")

            except Exception as e:
                logger.error(f"❌ 处理失败 [{post.id}]: {e}")
                continue

    # 保存已处理的帖子 ID
    if not args.dry_run:
        save_seen_post_ids(seen_ids)

    # 输出汇总
    logger.info("=" * 50)
    logger.info(f"📊 处理完成!")
    logger.info(f"   抓取: {total_fetched} 个帖子")
    logger.info(f"   过滤后: {total_filtered} 个")
    if not args.dry_run:
        logger.info(f"   已翻译: {total_translated} 个")
        logger.info(f"   草稿保存在: {output_dir}")


if __name__ == "__main__":
    main()
