---
layout: page
title: ログ一覧
permalink: /logs/
---

{% assign items = site.logs | sort: "date" | reverse %}
{% for item in items %}
- {{ item.date | date: "%Y-%m-%d" }} — [{{ item.title }}]({{ item.url }})
{% endfor %}
