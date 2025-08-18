---
layout: page
title: ログ一覧
permalink: /logs/
---

<style>
  ul.log-list { list-style:none; padding:0; margin:0; display:block; }
  ul.log-list > li { display:block; margin:0 0 1rem; padding:.4rem 0; border-bottom:1px solid #eee; }
  .log-date { color:#666; font-size:.9rem; display:block; }
  .log-title { font-size:1.05rem; text-decoration:none; }
</style>

{%- assign items = site.collections.logs.docs | sort: "date" | reverse -%}
<ul class="log-list">
{%- for item in items -%}
  <li>
    <span class="log-date">{{ item.date | date: "%Y-%m-%d" }}</span>
    <a class="log-title" href="{{ item.url | relative_url }}">🏃 {{ item.title }}</a>
  </li>
{%- endfor -%}
</ul>
