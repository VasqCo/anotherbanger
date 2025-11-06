---
layout: page
title: Blog
permalink: /blog/
nav_order: 50
---
{% assign posts = site.posts | where_exp: "post", "post.draft != true" %}
{% if posts == empty %}
<p>No posts yet.</p>
{% else %}
<ul style="padding-left:0; list-style:none;">
  {% for post in posts %}
    <li style="margin-bottom:2em;">
      <h2 style="margin-bottom:0.2em;"><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h2>
      <div style="color:#555; font-size:0.97em; margin-bottom:0.5em;">
        {% if post.author %}by {{ post.author }}, {% endif %}{{ post.date | date: "%B %-d, %Y" }}
      </div>
      {% if post.excerpt %}
        <div style="font-size:0.98em; color:#222;">{{ post.excerpt | strip_html | truncate: 180 }}</div>
      {% endif %}
    </li>
  {% endfor %}
</ul>
{% endif %}
