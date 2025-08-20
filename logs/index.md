---
layout: page
title: ログ一覧
permalink: /logs/
---

<style>
  .log-grid{display:grid;grid-template-columns:1fr;gap:12px;max-width:960px;margin:0 auto;padding:0}
  @media(min-width:720px){.log-grid{grid-template-columns:1fr 1fr}}
  .log-card{list-style:none;border:1px solid #eee;border-radius:12px;padding:12px;background:#fff}
  .log-date{color:#666;font-size:.85rem;display:block;margin-bottom:.2rem}
  .log-title{font-size:1.05rem;text-decoration:none;font-weight:600}
</style>

{%- assign items = site.logs | sort: "date" | reverse -%}
<ul class="log-grid">
{%- for item in items -%}
  <li class="log-card">
    <span class="log-date">{{ item.date | date: "%Y-%m-%d" }}</span>
    <a class="log-title" href="{{ item.url | relative_url }}">🏃 {{ item.title }}</a>
  </li>
{%- endfor -%}
</ul>
