---
layout: page
title: ログ一覧
permalink: /logs/
---

<style>
/* このページ専用の軽いスタイル（最小限） */
.log-list { list-style: none; padding: 0; margin: 0; }
.log-list li { margin: 0 0 1rem 0; padding: .4rem 0; border-bottom: 1px solid #eee; }
.log-list .date { color: #666; font-size: .9rem; display: block; }
.log-list .title { font-size: 1.05rem; text-decoration: none; }
</style>

{% assign items = site.logs | sort: "date" | reverse %}
<ul class="log-list">
{% for item in items %}
  <li>
    <span class="date">{{ item.date | date: "%Y-%m-%d" }}</span>
    <a class="title" href="{{ item.url | relative_url }}">🏃 {{ item.title }}</a>
  </li>
{% endfor %}
</ul>
