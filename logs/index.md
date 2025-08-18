---
layout: page
title: ログ一覧
permalink: /logs/
---

<style>
.post-list { list-style:none; padding:0; }
.post-list li { margin: 0 0 1rem; }
</style>

{% assign items = site.logs | sort: "date" | reverse %}
<ul class="post-list">
  {% for item in items %}
    <li>
      <span class="post-meta">{{ item.date | date: "%Y-%m-%d" }}</span>
      <h3><a href="{{ item.url | relative_url }}">{{ item.title }}</a></h3>
    </li>
  {% endfor %}
</ul>
