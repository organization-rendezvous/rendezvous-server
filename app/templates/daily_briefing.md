# {{ date }} 뉴스정리

{% for topic in topics %}

## {{ topic.topic_name }}

{% for trend in topic.trends %}

### {{ trend.title }}

- {{ trend.summary }}

키워드: {{ trend.keywords | join(', ') }}

{% for link in trend.links[:3] %}

- {{ link.title }} ({{ link.url }})
  {% endfor %}

---

{% endfor %}

{% endfor %}
