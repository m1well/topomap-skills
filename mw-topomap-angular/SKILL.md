---
name: mw-topomap-angular
description: Builds an interactive topomap of an Angular workspace - Nx monorepo, classic multi-project or a single app. Nx projects and libraries as outer frames, classes grouped by layer (route, page, organism, ui, state, data), inputs, outputs and public methods with a one-line purpose, labelled edges between projects, and clickable user journeys that light up the path from a route through the components into the state and out to the API. Written in four detail stages, each one openable on its own. The output is a model.json, opened at topomap.m1well.com. Use whenever someone wants to see, document or explain the structure, component tree, state flow or library boundaries of an Angular codebase. Also invoked via /mw-topomap-angular.
argument-hint: [project, scope or path to focus on, e.g. "erfassera" or "packages/shared" - empty means the whole workspace]
---

# Angular Diagram

Same renderer as the Spring Boot variant, different question. An Angular diagram
answers what nobody can grep out of a workspace:

1. which projects and libraries exist, and which may depend on which
2. what each class is - route, page, organism, ui piece, state, api
3. what a component takes in and gives out, and what a state service exposes
4. how a user journey travels: route → page → organism → state → api → backend

**Your job is the `model.json` - nothing else.** It is rendered at
topomap.m1well.com, which is not your concern here. Set `"preset": "angular"` in `meta`, otherwise you get the Spring columns.

The validator ships with this skill and is run from the analysed repo, so set the
path once:

```bash
SKILL=~/.claude/skills/mw-topomap-angular
```

## Workflow

**1. Ask for the language, then scope it.** Ask this **in English**, with
AskUserQuestion, English and German as options:

> In which language should the descriptions be written - the class summaries,
> method docs and edge labels?

That covers the content only; the page interface is always English. Record it as
`meta.language` and skip the question when the model already has it.

Then the scope, and in a monorepo this is the decision that makes or breaks the
diagram. **Count first** - the sweep in `references/extraction.md`, section 0,
prints files, components, injectables and routes per project, and a scope question
without those numbers is one nobody can answer.

`$ARGUMENTS` may name a project, a scope or a path. **A workspace with thirty
libraries does not fit in one picture.** Propose a split, with the counts next to
each option, and let the user pick:

- one diagram per product or scope (`apps/erfassera` plus the libraries it uses)
- one diagram per feature library, when a single library is the subject
- one overview diagram of the whole workspace with **only** the projects and their
  public entry points - no internal components at all

Say which one you built and what you left out.

**A single-app project becomes one lane - until that lane is too tall.** Above
roughly 40 classes, make the feature folders under `src/app/` the lanes instead
(`orders`, `admin`, `shared`), even though there is no Nx project behind them. Fifty
cards in one column is a lane nobody scrolls, and the 40-card rule further down
applies to a single app exactly like it applies to a workspace. Say in the report
that the lanes are folders, not projects - nothing enforces a folder boundary, so a
"cross-lane edge" there is an observation, not a violation.

**2. Map the projects.** See `references/extraction.md`. In Nx the project graph is
a command away, and the `tsconfig.base.json` paths tell you the public entry point
of every library. Those dependencies are the frame: an edge between two classes
that crosses a project boundary the graph does not have is either wrong or a
finding worth reporting - in Nx it usually means someone imported a deep path
instead of the barrel.

**3. Find the classes.** Decorators and directories, not file name suffixes -
modern Angular drops `.component.ts`, and both a state service and an api service
are `@Injectable`. The recipes are in `references/extraction.md`.

**4. Extract members and edges.** For a component: its `input()` / `output()`
signals and the public methods a template calls. For a state service: the signals
and resources it exposes plus the commands that mutate them. Edges come from
`inject()`, from constructor parameters, and from a parent template using a child's
selector - a template binding is an edge like any call.

Count what you extracted against what the file declares. The recipes here are greps,
and a grep that misses is silent: a component whose `input()`s are written on one
line, a method the pattern does not match, a state service whose signals sit in a
nested object. **Fewer members than declarations in the file is an extraction failure,
not a small class** - and nothing downstream catches it, because the model has no idea
what was in the file. A cheap counter-check per file:

```bash
grep -cE '= (input|output|model)(\.required)?<' path/to/component.ts
grep -cE '^\s+(readonly |protected |public )?[a-zA-Z]+\s*[=(]' path/to/state.ts
```

**5. Derive the user journeys - inventory first.** List every route in the
workspace, then every command a user can trigger (a form submit, a delete, a
filter). The default is one flow per route plus one per state-changing command.
Leave one out only when another flow already walks the identical chain. Say in the
report which ones you dropped and why.

**6. Write the model.** Field reference in `references/model-format.md`, stereotypes
and edge kinds in `references/extraction.md`, findings in `references/findings.md`.
Set `"preset": "angular"` and `"detail"` in `meta`. The files go to a dated folder,
`docs/mw-topomap-<date>/`, one per stage - see below.

**Before the first line of text: umlauts and accents are written out.** "Aufträge",
not "Auftraege". The file is UTF-8 and so is the renderer, so there is nothing to
work around - and a stage written in ASCII has to be gone through word by word
afterwards, which costs more than getting it right the first time. The full rule is
under "Rules that keep the diagram readable", and in Python it means
`ensure_ascii=False` on every `json.dump`.

Above roughly a hundred classes the file is no longer something you type. Write a
throwaway generator in the scratchpad, project by project, and dump the json with
`json.dump(model, fh, ensure_ascii=False, indent=1)`. The generator stays in the
scratchpad: what is delivered is the `model.json`, and later change requests are
patched into the json, never back into the generator.

Validate before you call a stage done. `validate.py` runs every check the renderer
runs plus two it does not, so a broken flow step surfaces here instead of
in a sidebar box nobody opens:

```bash
python3 $SKILL/assets/validate.py docs/mw-topomap-20260826/model-1.json
```

**7. Hand it over.** After every stage, not only at the end: say the file is
written, name it, and say what it now contains. It is opened at
**topomap.m1well.com** - the model is dropped onto the page and rendered in the
browser; nothing is uploaded and nothing is stored.

**8. Report.** File, counts (projects / classes / journeys / findings), the routes and
commands that did not get a flow with the reason, and every edge you were unsure
about. If a stage stayed under the findings floor, say which one and why - an honest
three beats a padded eight.


## Four stages, and you stop after any of them

A model for a real application is 60 to 100 KB of hand-written text, and that
writing is where the time goes - the analysis is quick by comparison. So it is
written in four passes, and after each one the file is **finished, named and
handed over** before anything else happens.

| stage | what goes in | share of the writing |
|-------|--------------|----------------------|
| **1** | modules, classes, stereotypes | ~10% |
| **2** | what each class offers: members, signatures, entity columns, plus the first findings | ~40% |
| **3** | the connections between them, with labels | ~10% |
| **4** | the use cases | ~40% |

Each stage is its own file - `model-1.json` through `model-4.json`, copied forward
and extended, so every stage stays openable on its own. Set `meta.detail` to the
stage you just finished; the page greys out what a model cannot do yet. At stage 1
the "connections" and "arrow labels" switches are disabled and the use case button
says "no use cases yet", so a half-finished model looks unfinished rather than
broken.

**After every stage, ask** with AskUserQuestion:

> Stage N is ready - <counts, findings included>. Continue to stage N+1, adjust the
> scope, or stop here?

Offer three options: continue, narrow the scope first (name what could go: a
module, a layer, the whole admin area), stop here. Anything the user cuts at stage 1
costs nothing to write later - which is the entire point of stopping to ask.

**Never run all four in one go without being told to.** A stage 4 model of a large
codebase takes a long time, and the most common answer after stage 1 is "leave
those three modules out".

## Where the files go

Everything lands in a **dated folder** in the analysed repo, one model per stage:

```
docs/mw-topomap-20260826/
  model-1.json   modules and classes
  model-2.json   + members, signatures, entity columns
  model-3.json   + connections with labels
  model-4.json   + use cases
```

**The date is the day the run started, and it is read, not remembered:**

```bash
date +%Y%m%d
```

Ask the shell once, before writing stage 1, and keep that folder for all four
stages - a stage 4 written a week later still belongs to the run that produced
stage 1. The same day goes into `meta.generated`, there in ISO form.

**One folder per run, and an old run is never touched.** If `docs/mw-topomap-*`
already exists, look before you write:

- continuing a run - the next stage, or a fix to a model that is already there -
  means staying in that folder
- a fresh look at the code means a new folder with today's date, and the old one
  stays exactly as it is

That is the whole point of the date: last quarter's picture stays openable next to
this one, and nobody has to remember to copy it somewhere safe first.

**Models only.** The skill writes json and nothing else - no html, no build step,
no tooling in the repo. The page lives at topomap.m1well.com.

**Copy, then extend.** Going from stage 2 to stage 3 means
`cp model-2.json model-3.json` and editing the copy - never editing model-2 in
place. Every stage stays on disk and stays openable, which is the whole point:
stage 1 is the picture you show someone in their first week, stage 4 is the one you
walk a use case through. Losing the earlier ones to get the later one would be a
bad trade.

## Rules that keep the diagram readable

- **Not every component.** A class earns a box by being a route target, a page, an
  organism, a state service, an api service, a guard, an interceptor, or by being
  used across a project boundary. A button atom used in forty places does not - put
  it in the ui column once, or leave it out and say so.
- **The barrel is the module api.** In Nx, what `index.ts` exports is the public
  surface of a library; everything else is internal. Route cross-project edges to
  the exported class. If a project reaches past a barrel into another library's
  internals, that is worth reporting.
- **State services carry the data.** Give every state service its signals and
  resources with types, the way an entity carries columns in the Spring variant.
  That is what makes the diagram double as a state overview.
- **Edge labels are half a sentence**, from the caller's point of view: "lädt die
  Wochen des Mandanten", "gibt den gewählten Filter nach oben". Not "calls
  load()". Under about 60 characters, otherwise the label gets cut off.
- **Findings are part of the model from stage 2 on.** A scan reads more of the
  codebase in one afternoon than most people read in a quarter, and what it notices
  on the way is thrown away unless it is written down. The patterns to look for, the
  categories and the floor per stage are in `references/findings.md`. Two rules
  decide whether the list is worth anything: every finding names a class, a count or
  a file, and none of them is advice that would have been true without opening the
  repo.
- **Language.** Summaries, docs, labels and notes in the language picked in step 1.
  Class, selector, signal and route names stay exactly as in the code.
- **Write the language properly.** Diacritics, accents and every other special
  character are spelled out: "Aufträge", "löst aus", "nächster Schritt" - never
  "Auftraege", "loest", "naechster". The file is UTF-8 and the renderer reads it as
  UTF-8, so there is nothing to escape around. In Python that means
  `ensure_ascii=False` on every `json.dump` - the default turns every umlaut into a
  `\uXXXX` escape.
- **A lane is a column of cards.** Above roughly 40 cards in one lane nobody scrolls
  it any more. That is the scope question from step 1 coming back: split the
  diagram, or show only the barrel exports of that library and say so in the report.


## Iterating

The model is the source of truth and belongs in the repo. On a change request -
a wrong edge, a missing component, another journey - patch the `model.json` of the
stage it belongs to, run `$SKILL/assets/validate.py` over it and hand it over again.
Regenerate from scratch only when the code has moved on.

If a stereotype is missing, declare it in `meta.stereotypes` (`model-format.md`) -
that is what the field is for, and it needs no change to topomap. If something still
cannot be expressed after that, say so in the report rather than bending the model
around it.
