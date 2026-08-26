---
name: mw-topomap-springboot
description: Builds an interactive topomap of a Spring Boot codebase - Kotlin or Java, Gradle or Maven, one module or twenty. Build modules as outer frames, classes grouped by stereotype (controller, module api, service, repository, entity), public methods with a one-line purpose, labelled call edges between modules, and clickable use cases that light up the path a request takes through the system. Written in four detail stages, each one openable on its own. The output is a model.json, opened at topomap.m1well.com. Use whenever someone wants to see, document or explain the architecture, module structure, call flow or database side of a Spring Boot project. Also invoked via /mw-topomap-springboot.
argument-hint: [module or package to focus on, e.g. ":customer" - empty means the whole app]
---

# Spring Boot Diagram

A Spring Boot diagram is not a UML class diagram. It answers the four questions
that actually come up on a modular Spring Boot codebase - Kotlin or Java, Gradle
or Maven, multi-module or a single one:

1. which build modules exist and what lives inside them
2. which class is what - controller, module api, service, repository, entity
3. what a class offers - its public methods and what each one is for
4. how a request travels - which module calls which, in what order

The renderer is not yours to touch. **Your job is to produce a `model.json`, not
HTML.** Never hand-write the page, never bend the model to work around the
renderer - fix the model instead.

The extractors and the validator ship with this skill and are run from the analysed
repo, so set the path once and use it in every command below:

```bash
SKILL=~/.claude/skills/mw-topomap-springboot
```

## Workflow

**1. Ask for the language.** The question is always asked **in English**:

> In which language should the descriptions be written - the class summaries,
> method docs and edge labels? (English / German / something else)

Ask it with AskUserQuestion, offering English and German as options; the user may
name any other language. This only covers the **content** written into the model.
The interface of the generated page - buttons, column headers, section titles - is
always English and is not up for discussion. Record the choice as `meta.language`
(an ISO code such as `en` or `de`) so a later run keeps writing in the same
language without asking again. If the model already carries `meta.language`, use
that and skip the question.

**2. Count, then ask about scope.** A scope question without numbers is a question
nobody can answer - "overview or everything?" means nothing until everything has a
size. The sweep is in `references/extraction.md`, section 0; it prints files,
controllers, services, repositories, entities and endpoints per module and takes
one call.

`$ARGUMENTS` may name a module or package to focus on. Empty means the whole app.
Put the numbers into the question: if the app has more than roughly 40 relevant
classes, propose a split (one diagram per bounded context, plus optionally one
overview diagram with only the module APIs) and let the user pick. Say what you
left out.

**3. Map the modules.** Gradle: `settings.gradle(.kts)` for the include list, then
each module's `build.gradle(.kts)` for the dependencies between them. Maven: the
`<modules>` block of the parent pom, then the `<dependency>` entries whose groupId
is the project's own.

**A single-module project becomes one lane - until that lane is too tall.** Above
roughly 40 classes, make the top level packages the lanes instead
(`com.acme.race`, `com.acme.auth`, `com.acme.billing`), even though there is only one
Gradle module. Fifty-five cards in one column is a lane nobody scrolls, and the
40-card rule further down applies to a single-module app exactly like it applies to a
modular one. Say in the report that the lanes are packages, not build modules - the
package graph is not enforced by anything, so a "cross-lane edge" there is an
observation, not a violation.
Module dependencies are the frame every class edge has to fit into: if a class edge
crosses a boundary the build files do not have, look twice - there are three shapes
that are allowed to, and they are listed in `references/extraction.md`.

**4. Find the classes.** See `references/extraction.md` for the grep recipes, the
name patterns you can drop without opening the file, and the three that look
droppable and are not. Skip utils, helpers, constants, DTO/record types, test code,
config that only wires beans.

**5. Extract members and edges.** Find the files with `rg`, then read them out with
the extractors in `assets/extract/` - a nineteen-parameter constructor and a
forty-column entity are not grep work:

```bash
python3 $SKILL/assets/extract/ctor.py   $(rg -l '@Service\b' --glob '**/*.kt') # dependencies
python3 $SKILL/assets/extract/funs.py   path/to/Service.kt                    # public methods
python3 $SKILL/assets/extract/entity.py $(rg -l '^@Entity\b' --glob '**/*.kt') # tables + columns
```

**All three write to stderr when they lose something, and that is the half you must
not skip:** `funs.py` says when it printed fewer methods than the file declares,
`entity.py` says which entities came back with zero columns and which column types it
could not map. Fewer methods than `fun` in the file means the extraction failed, not
that the class is small - and nothing downstream can catch it, because the model has
no idea how many methods there were. Read the file by hand when it fires.

Their output is raw material, not the model: the `doc` line, the summary and every
edge label are yours to write. Public functions get a one-line purpose in your own
words, not a copy of the KDoc. Edges come from constructor injection, event
publish/listen pairs and repository access. Every cross-module edge gets a label
saying what it fetches or does.

**6. Derive the use cases - inventory first.** List *every* entry point before
writing a single flow: every `@*Mapping`, every listener, every `@Scheduled`. The
recipe is in `references/extraction.md`. Behind every endpoint sits something a
person wanted to do, so the list of candidates is the list of endpoints - not a
handful you happened to notice.

Every flow gets a `description`: one or two sentences on what this use case is for
and the one thing about it worth knowing - a guard, an order of operations, a
fallback. That text is what the reader picks from in the use case modal, so
"loads the customers" is wasted space; "six checks before the insert: overlap,
already booked, writable month" is not.

**The default is one flow per entry point.** You need a reason to leave one out,
not a reason to include it - the list of endpoints *is* the list of use cases,
because someone wanted each of them badly enough to build it. Leave one out only
when it calls no service at all (an endpoint returning a constant or an enum), or
when a different flow already walks the identical chain of edges with identical
notes. "It is only a read" is not a reason: a read shows which repository answers
it, and that is exactly what people look this up for.

Forty endpoints means somewhere around forty flows. They live in a scrollable
modal, so a long list costs nothing - a thin diagram costs a lot. The report names
every entry point that did not get a flow, with the reason.

**7. Write the model.** Field reference in `references/model-format.md`, stereotypes
and edge kinds in `references/extraction.md`, findings in `references/findings.md`.
Set `"preset": "spring"` and `"detail"` in `meta`. The files go to a dated folder,
`docs/mw-topomap-<date>/`, one per stage - see below.

**Before the first line of text: umlauts and accents are written out.** "Aufträge",
not "Auftraege". The file is UTF-8 and so is the renderer, so there is nothing to
work around - and a stage written in ASCII has to be gone through word by word
afterwards, which costs more than getting it right the first time. The full rule is
under "Rules that keep the diagram readable", and in Python it means
`ensure_ascii=False` on every `json.dump`.

Above roughly a hundred classes the file is no longer something you type. Write a
throwaway generator in the scratchpad, module by module, and let it dump the json
with `json.dump(model, fh, ensure_ascii=False, indent=1)` - **`ensure_ascii=False`
is not optional**, see the language rule below.

> The generator is scratchpad tooling and stays there. What is delivered and
> checked in is the `model.json`. Later change requests are patched into the json,
> never into the generator - two sources of truth is how the file and the picture
> start drifting apart.

Validate before you call a stage done. `validate.py` runs every check the renderer
runs, plus the two it does not, and it fails loudly instead of hiding a note in a
sidebar box nobody opens:

```bash
python3 $SKILL/assets/validate.py docs/mw-topomap-20260826/model-1.json
```

**8. Hand it over.** After every stage, not only at the end: say the file is
written, name it, and say what it now contains. It is opened at
**topomap.m1well.com** - the model is dropped onto the page and rendered in the
browser; nothing is uploaded and nothing is stored.

**9. Report.** Name the files that now exist in the dated folder, the counts
(modules / classes / flows / findings), the entry points that did not get a flow with
the reason, and which edges you were unsure about. If a stage stayed under the
findings floor, say which one and why - an honest three beats a padded eight. A
wrong edge presented confidently is worse than a missing one.


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

- **Not every class.** A class earns a box by being a stereotype (controller, api,
  service, repository, entity, client, listener, mapper, job) or by being called
  across a module boundary. Everything else stays out - the name patterns that
  never earn one are listed in `references/extraction.md`.
- **What runs before the controller, and what sits on the other end.** Two shapes
  the `spring` preset has no stereotype for, both declared in `meta.stereotypes` and
  spelled out in `references/extraction.md`: `guard` for filters, interceptors and
  authorisation aspects - they run *before* the entry point, so they belong in column
  0 next to `job`, and giving them `service` puts them behind the controller they run
  in front of. And `external` for the system an `http` edge points at - OpenRouter,
  Idently, Stripe - one node per system in a lane of its own at the end. Without it
  the calls that leave the process have no arrow at all, and those are usually the
  ones worth looking at.
- **The module api is the point.** If a module has a facade or api class that other
  modules go through, give it the `api` stereotype and route cross-module edges to
  it, not to the internals behind it. If a module has no such class, that is worth
  saying in the report - it usually means the boundary leaks.
- **An interface and its implementation.** One box, not two - *unless* the
  interface is the module's public api, which in a modular codebase is the normal
  case rather than the exception: `CustomerFacade` in the shared module,
  `CustomerFacadeImpl` in the module that owns it. Then the interface is `api`, the
  impl is `service`, cross-module edges point at the **interface**, and one edge
  `interface -> impl` carries the label `implemented by`. In a cross-module flow
  that edge is a **step of its own** - skip it and the flow jumps from the caller
  straight into the impl, which is an edge that does not exist, and the renderer
  drops the step.
- **Entities carry the database.** Give every entity its table name and its columns
  with types, mark PK and FK. The card shows the table name, the columns appear in
  the inspector - so a schema of forty columns costs no space in the picture. An
  entity with zero columns is an extraction failure, not an empty table.
- **Edge labels are half a sentence**, from the caller's point of view: "loads the
  active tenant", "publishes CustomerCreated". Not "calls findById". Keep them
  under about 60 characters - a label sits on an arrow between two cards and is cut
  off with an ellipsis beyond roughly that. The same goes for a flow step's `note`,
  which replaces the label while that flow is active.
- **Method docs are one line**, what it does and the notable edge case: "returns a
  page of customers for the tenant, empty page when the tenant is unknown".
- **Findings are part of the model from stage 2 on.** A scan reads more of the
  codebase in one afternoon than most people read in a quarter, and what it notices
  on the way is thrown away unless it is written down. The patterns to look for, the
  categories and the floor per stage are in `references/findings.md`. Two rules
  decide whether the list is worth anything: every finding names a class, a count or
  a file, and none of them is advice that would have been true without opening the
  repo.
- **Language.** Summaries, method docs, edge labels and flow notes go in the
  language picked in step 1 - never mixed. Class, method, table and column names
  always stay exactly as they are in the code, whatever that language is. Anything
  that is part of the tool rather than the model stays English.
- **Write the language properly.** Diacritics, accents and every other special
  character are spelled out: "Aufträge", "löst aus", "nächster Schritt" - never
  "Auftraege", "loest", "naechster". The model file is UTF-8 and the renderer reads
  it as UTF-8, so there is nothing to escape around. In Python that means
  `ensure_ascii=False` on every `json.dump`; the default silently turns every umlaut
  into a `\uXXXX` escape.
- **A lane is a column of cards.** Above roughly 40 cards in one lane the picture
  gets tall enough that nobody scrolls it any more. That is not a layout bug, it is
  the signal from step 2 coming back: split the diagram, or collapse the lane by
  showing only its api classes and saying so in the report.

## Iterating

The model is the source of truth and is meant to be kept in the repo. On a change
request - a wrong edge, a missing class, another use case - patch the `model.json`
of the stage it belongs to, run `validate.py` over it, and hand it over again. Do not regenerate the whole model from scratch unless the code moved on.

If a stereotype is missing, declare it in `meta.stereotypes` (`model-format.md`) -
that is what the field is for, and it needs no change to topomap. If something still
cannot be expressed after that - a column with nowhere to go, an edge kind that does
not exist - that is a topomap issue, not a reason to bend the model. Say so in the
report.
