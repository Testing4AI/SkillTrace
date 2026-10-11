# A small, inspectable example gallery

The release contains two authored seeds and four deliberately constructed variants.
Their purpose is to show what each trace represents, how to inspect matching evidence,
and how the cached audit works. They are not original benchmark samples or automatically
generated LLM outputs. Their SOG annotations were manually specified against their
source text and validated with the same public schema used for LLM extraction.

## 1. PDF form processing

The [seed](../examples/form/seed/SKILL.md) describes five steps:
inspect fields → validate input → fill → read back → export.

The [paraphrase](../examples/form/paraphrase/SKILL.md) changes the wording and delegates
implementation to the host. Implementation is therefore inapplicable for that pair.
The [implementation-lift variant](../examples/form/implementation_lift/SKILL.md)
changes the prose but retains the seed's executable recipe in a plain-text support
document. This exercises code extraction from documents, not just source extensions.

| Normalized field | Seed's validation block | Paraphrase's validation block |
| :--- | :--- | :--- |
| action | validate | validate |
| object_role | record | record |
| tool_role | schema_validator | schema_validator |
| inputs | record, field_inventory | record, field_inventory |
| outputs | validated_record | validated_record |

Source evidence differs:

> Seed: “Validate the record against that inventory; stop if a required field is absent.”

> Variant: “Check the entries against those slots and reject incomplete mandatory entries.”

The matching fields abstract the operation. Exact quotes remain available to check
whether that abstraction is justified. The resource relation from validation to
`validated_record`, and the filling operation's consumption of that role, connect
the same workflow choice across different words.

## 2. Market watchlist

The [seed](../examples/watchlist/seed/SKILL.md), [English rewrite](../examples/watchlist/rewrite/SKILL.md)
and [Chinese translation](../examples/watchlist/translation/SKILL.md) describe:

* a reduced analysis mode that bypasses news retrieval;
* a separate alert entry point;
* loading a persistent watchlist and conditions;
* comparing conditions with observations before reporting alerts.

These normalized relations survive the constructed transformations:

```text
select mode ── bypass [reduced_analysis_mode] ──▶ retrieve news

alert request ── enters ──▶ load watchlist ── next ──▶ check conditions ── next ──▶ report
                                                         │
                            consumes watchlist_condition ─┤
                            consumes market_observation ──┤
                            produces alert_result ────────┘
```

In the JSON convention, every resource relation is written from its operation to
the role, with its relation type identifying consumption or production. A bypass
edge records the operation skipped under its condition; it is not an execution edge.

The manually supplied, shared-role annotations make the operational correspondence
explicit. An O score of 1 on these examples reflects identical annotations by
construction, not an observed claim that an LLM always extracts identical graphs.

## Inspect and regenerate

```bash
python3 scripts/build_showcase.py
python3 scripts/run_demo.py
```

`build_showcase.py` contains the complete annotation specification. It checks that
each quote appears in its package and generates the six SOG files and caches.
No hidden dataset, model access, or downloads are involved. Demo outputs list raw
scores separately from the normalized MaxFusion ratio, which may exceed one.

To test extraction rather than matching, register each side independently using the
LLM path described in [METHOD.md](METHOD.md), then inspect the returned annotations.
