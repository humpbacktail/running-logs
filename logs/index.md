---
layout: page
title: ログ一覧
permalink: /logs/
---

<style>
  .log-grid{display:grid;grid-template-columns:1fr;gap:12px;max-width:960px;margin:0 auto;padding:0}
  @media(min-width:720px){.log-grid{grid-template-columns:1fr 1fr}}
  .log-card{list-style:none;border:1px solid #eee;border-radius:12px;padding:14px 16px;background:#fff;display:flex;align-items:center;gap:14px}
  .log-date{color:#999;font-size:.8rem;white-space:nowrap;flex-shrink:0;font-family:'Space Mono',monospace}
  .log-title{font-size:1rem;text-decoration:none;font-weight:600;line-height:1.4}
</style>

{%- assign items = site.logs | sort: "date" | reverse -%}
<ul class="log-grid">
{%- for item in items -%}
  <li class="log-card">
    <span class="log-date">{{ item.date | date: "%Y-%m-%d" }}</span>
    <a class="log-title" href="{{ item.url | relative_url }}">{{ item.title }}</a>
  </li>
{%- endfor -%}
</ul>
