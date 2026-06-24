# Reddit → 小红书 内容管道

从 Reddit 热门帖子（生活技巧类）抓取优质内容，通过 AI 翻译改编为小红书风格的中文草稿，保存到本地供手动发布。

## 功能

- 📥 从多个 subreddit 抓取热门帖子（r/LifeProTips, r/YouShouldKnow 等）——直接解析网页，无需 Reddit API
- 🔍 智能过滤：分数、好评率、NSFW、去重
- 🤖 AI 翻译 + 小红书风格改编（emoji、话题标签、亲切语气）
- 📝 生成可直接使用的小红书草稿（Markdown/JSON）
- 🔄 去重机制：不会重复处理已抓取的帖子
- 🔌 支持多个 LLM 提供商（DeepSeek / MiniMax / 小米 MiMo / 自定义）

## 快速开始

### 1. 安装依赖

```bash
cd reddit
pip install -e .
```

### 2. 配置 API 凭证

复制 `.env.example` 为 `.env`，填入你的 LLM API Key：

```bash
cp .env.example .env
```

**只需要一个 LLM API Key**，Reddit 抓取不需要任何凭证（直接解析公开网页）。

| 服务 | 是否需要 Key | 获取方式 |
|------|-------------|---------|
| Reddit 抓取 | ❌ 不需要 | 直接抓取公开页面 |
| LLM 翻译 | ✅ 需要 | 根据下方选择的 provider 获取 |

### 3. 选择 LLM 提供商

编辑 `config/settings.yaml`，修改 `provider` 字段：

```yaml
translation:
  provider: "deepseek"     # 改这里切换模型
  api_key_env: "LLM_API_KEY"
  max_tokens: 4096
```

内置预设：

| provider | 平台 | 默认模型 | API Key 获取 |
|----------|------|---------|-------------|
| `deepseek` | DeepSeek | deepseek-chat | https://platform.deepseek.com |
| `minimax` | MiniMax | MiniMax-Text-01 | https://platform.minimaxi.com |
| `xiaomi` | 小米 MiMo | MiMo-7B | https://dev.mi.com |
| `custom` | 自定义 | 需手动填写 | — |

自定义 provider 示例：

```yaml
translation:
  provider: "custom"
  base_url: "https://你的API地址/v1"
  model: "你的模型名"
  api_key_env: "LLM_API_KEY"
```

如果想用预设但换模型，直接填 `model` 覆盖默认值：

```yaml
translation:
  provider: "deepseek"
  model: "deepseek-reasoner"    # 覆盖默认的 deepseek-chat
```

### 4. 运行

```bash
# 先试运行（只抓取和过滤，不翻译，不花钱）
python -m src.main --dry-run

# 限制每个 subreddit 只处理 5 个帖子（省钱测试）
python -m src.main --limit 5

# 正式运行
python -m src.main
```

### 5. 查看草稿

生成的草稿保存在 `data/drafts/` 目录下，每个帖子一个 Markdown 文件，包含：
- 中文标题（带 emoji）
- 结构化中文正文
- 小红书话题标签
- 原文链接和信息

## 配置说明

完整配置文件 `config/settings.yaml`：

```yaml
reddit:
  subreddits:
    - name: "LifeProTips"
      sort: "top"            # top/hot/new/rising
      time_filter: "week"    # hour/day/week/month/year/all
      limit: 20
  min_score: 500
  min_upvote_ratio: 0.85
  exclude_nsfw: true
  exclude_stickied: true
  min_text_length: 100

translation:
  provider: "deepseek"       # deepseek / minimax / xiaomi / custom
  model: ""                  # 留空用预设默认，或填写自定义模型名
  api_key_env: "LLM_API_KEY" # .env 中的环境变量名
  max_tokens: 4096

output:
  format: "markdown"         # markdown 或 json
  directory: "data/drafts"
  include_original: true     # 是否保留英文原文
```

## 项目结构

```
reddit/
├── config/settings.yaml    # 配置文件
├── src/
│   ├── main.py             # CLI 入口
│   ├── reddit_scraper.py   # Reddit 抓取
│   ├── content_filter.py   # 质量过滤 + 去重
│   ├── translator.py       # AI 翻译（支持多 provider）
│   ├── formatter.py        # 草稿格式化 + 输出
│   └── models.py           # 数据模型
├── data/
│   ├── seen_posts.json     # 去重状态
│   └── drafts/             # 生成的草稿
└── .env                    # API 凭证（不要提交到 git）
```
