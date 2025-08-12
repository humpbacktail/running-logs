---
layout: page
title: ログ一覧
permalink: /logs/
---

{% assign items = site.logs | sort: "date" | reverse %}

<ul class="post-list">
{% for item in items %}
  <li>
    <span class="post-meta">{{ item.date | date: "%Y-%m-%d" }}</span>
    <h3><a href="{{ item.url | relative_url }}">{{ item.title }}</a></h3>
  </li>
{% endfor %}
</ul>
