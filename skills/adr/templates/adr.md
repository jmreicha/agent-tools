{% if is_ng %}---
number: {{ number }}
title: {{ title }}
date: {{ date }}
status: {{ status | lower }}
{% if links %}links:
{% for link in links %}  - target: {{ link.target }}
    kind: {{ link.kind | lower }}
{% endfor %}{% endif %}{% if tags %}tags:
{% for tag in tags %}  - {{ tag }}
{% endfor %}{% endif %}---

{% endif %}# {{ number }}. {{ title }}

Date: {{ date }}

## Status

{{ status }}
{% for link in links %}
{{ link.kind }} [{{ link.target }}. {{ link.target_title }}]({{ link.target_filename }})
{% endfor %}
## Context

{{ context if context else "The problem or force that makes a decision necessary now, with the facts and constraints that shape it." }}

## Decision

{{ decision if decision else "What we decided, stated as an action: \"We use X for Y.\"" }}

## Alternatives

Each option we considered and rejected, with the reason in one line.

## Consequences

{{ consequences if consequences else "What gets easier, what gets harder, and what we now have to do or watch." }}
