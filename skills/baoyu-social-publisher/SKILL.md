---
name: baoyu-social-publisher
description: >
  社交媒体多平台发布 — 支持微信公众号（文章+图文）、微博（文字+图片+视频+头条文章）、
  X/Twitter（posts+X Articles）。Markdown输入自动转换，微信场景默认将外部链接转为底部引用。

  触发词 (中文): 发布公众号、微信公众号发文、post to wechat、写公众号文章、
  发微博、微博头条文章、发布到微博、post to Weibo、写微博、
  发推特、发X、post to X、tweet、publish to Twitter、share on X、
  markdown转HTML、md转微信格式、微信外链转底部引用。

  Trigger (EN): post to WeChat Official Account, publish to WeChat,
  post to Weibo, publish to Weibo, share on Weibo,
  post to X, tweet, publish to Twitter, share on X, X Article,
  markdown to WeChat HTML, social media publishing.

  小红书图片卡片 → baoyu-xhs-images。
version: "2.0.0"
user-invocable: true
---

# Social Publisher

一站式社交媒体发布。支持微信公众号、微博、X/Twitter 三平台。

## 平台路由

| 用户意图 | 平台 | 发布方式 |
|---------|------|---------|
| 公众号/微信文章 | WeChat Official Account | API 或 Chrome CDP |
| 微信贴图/图文 | WeChat Official Account | Chrome CDP (多图) |
| 微博/头条文章 | Weibo | Chrome CDP |
| X/Twitter/推文 | X (Twitter) | Chrome CDP 或 API |
| MD转HTML | 微信格式化 | Markdown → WeChat HTML |

## 微信公众号

文章模式支持 HTML/Markdown/纯文本输入。Markdown 文章默认将普通外链转为底部引用（WeChat-friendly）。
贴图模式支持多图发布。

## 微博

支持普通贴文（文字+图片+视频）和头条文章（Markdown via Chrome CDP）。

## X / Twitter

支持普通推文（图片/视频）和 X Articles（长文 Markdown）。

## Markdown → WeChat HTML

独立格式化：支持代码高亮、数学公式、Mermaid（via headless Chrome 渲染PNG）、PlantUML、脚注、Alert、信息图、底部引用。
