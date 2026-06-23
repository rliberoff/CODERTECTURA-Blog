# Graph Report - .  (2026-06-15)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 283 nodes · 453 edges · 35 communities (30 shown, 5 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 19 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c0620d77`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]

## God Nodes (most connected - your core abstractions)
1. `n()` - 19 edges
2. `i()` - 11 edges
3. `g()` - 11 edges
4. `c()` - 9 edges
5. `k()` - 9 edges
6. `r()` - 8 edges
7. `m()` - 8 edges
8. `y()` - 8 edges
9. `iframe()` - 8 edges
10. `Footer Component` - 8 edges

## Surprising Connections (you probably didn't know these)
- `g()` --calls--> `T()`  [INFERRED]
  js/lunr/lunr.tr.min.js → js/main.min.js
- `Main Homepage Template` --references--> `Base HTML Structure`  [EXTRACTED]
  index.html → _default/baseof.html
- `Base HTML Structure` --implements--> `Header Navigation Component`  [EXTRACTED]
  _default/baseof.html → partials/header.html
- `Single Post/Page Template` --implements--> `Post Card Component`  [INFERRED]
  _default/single.html → partials/post-card.html
- `Callout Shortcode Block` --semantically_similar_to--> `Notice/Alert Shortcode`  [AMBIGUOUS] [semantically similar]
  shortcodes/callout.html → shortcodes/notic.html

## Import Cycles
- None detected.

## Communities (35 total, 5 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.21
Nodes (30): d(), a(), b(), c(), d(), E(), er(), f() (+22 more)

### Community 1 - "Community 1"
Cohesion: 0.14
Nodes (20): appendQueryParams(), currentInstance(), error(), facebookvideoHandler(), factory(), googlemapsHandler(), handleTabKey(), iframe() (+12 more)

### Community 2 - "Community 2"
Cohesion: 0.15
Nodes (10): c(), E(), f(), I(), l(), n(), p(), S() (+2 more)

### Community 3 - "Community 3"
Cohesion: 0.19
Nodes (14): a(), c(), d(), e(), f(), l(), m(), n() (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.24
Nodes (13): a(), b(), c(), d(), e(), h(), i(), l() (+5 more)

### Community 5 - "Community 5"
Cohesion: 0.22
Nodes (12): a(), c(), e(), f(), i(), k(), l(), m() (+4 more)

### Community 6 - "Community 6"
Cohesion: 0.22
Nodes (13): a(), d(), e(), f(), i(), l(), m(), o() (+5 more)

### Community 7 - "Community 7"
Cohesion: 0.23
Nodes (12): a(), c(), d(), i(), l(), m(), n(), o() (+4 more)

### Community 8 - "Community 8"
Cohesion: 0.28
Nodes (13): a(), c(), d(), f(), i(), k(), l(), m() (+5 more)

### Community 9 - "Community 9"
Cohesion: 0.23
Nodes (13): a(), c(), e(), f(), i(), l(), m(), o() (+5 more)

### Community 10 - "Community 10"
Cohesion: 0.33
Nodes (10): a(), c(), d(), l(), m(), n(), o(), r() (+2 more)

### Community 11 - "Community 11"
Cohesion: 0.23
Nodes (6): i(), l(), n(), s(), t(), u()

### Community 12 - "Community 12"
Cohesion: 0.33
Nodes (7): a(), c(), e(), i(), s(), t(), u()

### Community 16 - "Community 16"
Cohesion: 0.83
Nodes (3): hideToc(), showToc(), toggleToc()

### Community 27 - "Community 27"
Cohesion: 0.22
Nodes (9): Footer Component, GitHub Social Link, Head Meta Tags & Resources, LinkedIn Social Link, RSS Feed Link, Threads Social Link, Twitch Social Link, X (Twitter) Social Link (+1 more)

### Community 28 - "Community 28"
Cohesion: 0.25
Nodes (8): About Page Template, Base HTML Structure, Header Navigation Component, Main Homepage Template, List View Template, Pagination Controls, Post Card Component, Single Post/Page Template

### Community 29 - "Community 29"
Cohesion: 0.33
Nodes (6): AI-Assisted Flag, Categories Metadata, Date Field, Draft Status Flag, Posts Template, Tags Metadata

### Community 30 - "Community 30"
Cohesion: 0.40
Nodes (5): About Page, Hugo Static Site Framework, Layout Field, Slug Field, URL Field

## Ambiguous Edges - Review These
- `Callout Shortcode Block` → `Notice/Alert Shortcode`  [AMBIGUOUS]
   · relation: semantically_similar_to

## Knowledge Gaps
- **28 isolated node(s):** `Slug Field`, `URL Field`, `Layout Field`, `Avatar Field`, `Date Field` (+23 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Callout Shortcode Block` and `Notice/Alert Shortcode`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `g()` connect `Community 0` to `Community 2`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Why does `y()` connect `Community 0` to `Community 2`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `p()` connect `Community 2` to `Community 0`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `g()` (e.g. with `d()` and `f()`) actually correct?**
  _`g()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Slug Field`, `URL Field`, `Layout Field` to the rest of the system?**
  _29 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.14130434782608695 - nodes in this community are weakly interconnected._