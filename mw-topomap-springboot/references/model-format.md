# The model file

A topomap is one json file. This is every field it may contain; the stereotypes and
edge kinds for this stack are in `extraction.md`.

The file is the whole deliverable - it is dropped onto **topomap.m1well.com**, which
renders it in the browser without uploading anything. Nothing here builds a page.

```jsonc
{
  "meta": {
    "title": "acme-platform",        // shown in the title bar and the browser tab
    "preset": "spring",             // stereotype set and column layout
    "generated": "2026-08-25",
    "notes": "free text",
    "language": "de",               // language of the descriptions in this model,
                                    // asked once and reused on the next run
    "detail": 2,                    // how far the model got: 1 modules+classes,
                                    // 2 +members, 3 +edges, 4 +flows. The renderer
                                    // disables whatever has no data behind it.
    "stereotypes": {                 // optional, adds a stereotype the preset has not
      "guard": { "label": "guard", "rank": 0,
                 "icon": "shield", "color": "var(--mw-warning-color)" }
    },
    "theme": {                       // optional, retunes the MaverickWave palette
      "primary": "#0f766e",          // every derived tone follows, same as the framework
      "secondary": "#b45309",
      "success": "#15803d", "warning": "#a16207",
      "danger": "#b91c1c", "info": "#0e7490", "gray": "#64748b",
      "background": "#0b111a", "text": "#d6dbdf", "accentText": "#efefef",
      "fontBase": "'Inter', sans-serif", "fontMono": "'JetBrains Mono', monospace"
    }
  },

  "modules": [                        // the outer frames, one lane each, in this order
    {
      "id": "customer-core",          // referenced by node.module
      "name": ":customer:core",       // gradle path, shown as the lane title
      "path": "customer/core",        // directory, shown small next to the title
      "description": "customer domain + persistence"
    }
  ],

  "nodes": [                          // the classes
    {
      "id": "CustomerFacade",         // unique, referenced by edges
      "module": "customer-core",
      "name": "CustomerFacade",       // shown on the card
      "stereotype": "api",            // drives colour, icon and column - see extraction.md
      "tags": ["cached"],             // optional extra badges - also the place for
                                      // "19 dependencies" or "@Scheduled"
      "fqn": "com.acme.customer.CustomerFacade",
      "file": "customer/core/src/main/kotlin/com/acme/customer/CustomerFacade.kt",
      "summary": "one or two sentences on what this class is for",
      "rank": 1,                      // optional, overrides the column of the stereotype
      "members": [
        {
          "name": "findAll",                                        // used by flow.entry
          "signature": "findAll(tenantId: TenantId): Page<Customer>",
          "http": "GET /api/customers",                             // controllers and clients only
          "doc": "one line on what it does and the notable edge case"
        }
      ],
      "table": "customer",            // entities only, shown on the card
      "columns": [                    // entities only, shown in the inspector
        { "name": "id", "type": "uuid", "pk": true },      // from the @MappedSuperclass
        { "name": "tenant_id", "type": "uuid", "fk": true }
      ]
    }
  ],

  "edges": [                          // the arrows, direction is from -> to
    {
      "id": "e1",                     // referenced by flow steps, keep it stable
      "from": "CustomerController",
      "to": "CustomerFacade",
      "kind": "call",                 // call | http | event | persist | maps
      "label": "loads the customers of the tenant"
    }
  ],

  "flows": [                          // the clickable use cases
    {
      "id": "get-all-customers",
      "name": "GET /api/customers",   // shown in the use case modal
      "description": "one or two sentences: what it is for, plus the one thing worth knowing about it",
      "color": "var(--mw-ink-primary)", // optional, auto-assigned from the palette;
                                        // use an --mw-ink-* token, not a raw brand
                                        // colour, or the line disappears on the page
      "entry": "CustomerController#getAll",   // nodeId#memberName, highlights that method
      "steps": [
        { "edge": "e1", "note": "controller hands over the tenant id" },
        { "from": "CustomerFacade", "to": "CustomerService" }        // alternative to "edge"
      ]
    }
  ],

  "findings": [                       // what the scan noticed on the way, from stage 2 on
    {
      "id": "f1",                     // unique, stable
      "title": "one line, the observation itself",
      "severity": "medium",           // high | medium | low
      "category": "coupling",         // see findings.md
      "stage": 2,                     // the stage it became visible in
      "nodes": ["CustomerService"],   // node ids - at least one node or module
      "modules": ["customer-core"],   // module ids, when it is about a whole lane
      "evidence": "19 constructor parameters, 640 lines",   // counts from the code, not translated
      "detail": "one to three sentences: what it is, and what it costs",
      "suggestion": "optional, the obvious cut"
    }
  ]
}
```

## Custom stereotypes

`meta.stereotypes` is how a class gets a column and a colour the preset does not
have. The renderer builds its table from the preset first and lays this object over
it, so a key the preset does not know becomes a real stereotype instead of landing in
the "model issues" box as `unknown stereotype ... - shown as component`.

```jsonc
"stereotypes": {
  "guard": { "label": "guard", "rank": 0, "icon": "shield", "color": "var(--mw-warning-color)" }
}
```

| field | default if left out | what it drives |
|---|---|---|
| `label` | the key itself | the line under the class name, the sidebar filter, the inspector, the search |
| `rank` | `2` | the column the card lands in, and the order of the filter list |
| `icon` | `cube` | the icon on the card |
| `color` | `var(--mw-gray-color)` | stripe, icon, badges, table name, and the tint behind an `http` chip |

Three things that cost time if nobody says them:

- **It replaces, it does not merge.** An entry for a key the preset already has throws
  that whole definition away. Writing `"service": { "color": "..." }` to retint the
  services gets you label `service`, rank 2 and the cube icon along with it. **Always
  write all four fields.**
- **Column headers come from the preset, not from here.** A `rank` beyond the six
  preset columns works, but its header reads `Rank 6`. Put a custom stereotype in one
  of the ranks 0 to 5 that already has a name.
- **The colour is not drawn raw.** It is set as `--st`, and the css clamps the
  lightness into the readable band for the active theme. Any css colour works,
  `var(--mw-*)` and `color-mix()` included - which is what keeps a `meta.theme`
  override working.

Icons that exist: `globe`, `door`, `gear`, `cube`, `shuffle`, `cloud`, `bolt`,
`clock`, `sliders`, `db`, `table`, `signpost`, `shield`, `window`, `layout`,
`puzzle`, `dot`, `wand`. An unknown name falls back to `cube` silently, so
`validate.py` checks the spelling - the renderer will not.

## Findings

Everything the scan noticed while reading, anchored to the classes it is about. The
patterns worth writing down, the categories and how many belong in each stage are in
`findings.md`.

- `nodes` and `modules` are the anchor: the renderer can highlight what a finding is
  about, the same way a flow highlights its path. At least one of the two is required.
- `evidence` holds the counts and identifiers that made it a finding. It stays in the
  code's own words; `title`, `detail` and `suggestion` are written in the model
  language like everything else.
- `stage` says when it became visible - size at stage 2, coupling at stage 3, order
  and guards at stage 4. It is also why a stage 4 model carries more findings than a
  stage 2 one.
- Findings are optional and additive, so a model without them keeps rendering.

## Entity columns

The columns are the schema, so two of them are not in the entity file at all:

- **The audit columns** - `id`, `created_*`, `updated_*`, the soft-delete pair -
  come from the `@MappedSuperclass` base class. Read each base once and prepend its
  columns to every entity that extends it. Without them half the tables have no
  primary key.
- **A `@Inheritance(JOINED)` child** carries only its own columns plus the inherited
  `id`. The relation is an edge `child -> base`, `kind: "persist"`, label
  `@Inheritance JOINED`.

An entity with zero columns means the extraction failed, never that the table is
empty.

## Flows

- Steps are ordered. The number on the edge label is the step index.
- The same edge may appear in several flows and more than once in one flow. Twice
  in one flow is how an order of operations becomes visible: the client that pulls
  the attachments in step 2 and acknowledges the message in step 9 walks the same
  arrow, and the two notes say which is which.
- A step's `note` replaces the edge label while that flow is active, so the same
  edge can read differently in a read flow and in a write flow.
- Edges not in the active flow fade out, classes not touched by it dim down.

## Detail stages

A model is written in four passes, each one a file of its own:

| `meta.detail` | contains |
|---|---|
| 1 | modules, classes, stereotypes |
| 2 | plus members, signatures, entity columns |
| 3 | plus edges with labels |
| 4 | plus flows |

The renderer does not trust the number - it looks at what is in the model and
disables what has no data behind it, so an unfinished model renders as unfinished
rather than as broken.

## Before handing a stage over

`$SKILL/assets/validate.py` runs every check the renderer runs on load, plus a duplicate
edge id check and an entity column check that it does not. Errors mean the picture
would show something other than the model says; warnings mean it renders worse than
intended.

```bash
python3 $SKILL/assets/validate.py docs/mw-topomap-20260826/model-4.json
```

Write the file with `ensure_ascii=False`, otherwise every umlaut ends up as a
`\uXXXX` escape in a file that is UTF-8 anyway.

## Compatibility

New fields are optional, always. A model written a year ago keeps rendering: the
renderer repairs what it can and lists the rest in a "model issues" box in the
panel - worth reading after opening a fresh model.
