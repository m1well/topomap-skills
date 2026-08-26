# Findings - what to write down while reading

A scan reads more of the workspace in an afternoon than most people read in a
quarter, and everything it notices on the way is thrown away the moment the model is
written. `findings` is where that goes: the things that stood out, with the number
that made them stand out.

**A finding is an observation, not advice.** "The page component is 610 lines and
injects four api services" is a finding. "Consider keeping components small" is a
fortune cookie - true without ever having opened the repo, and exactly what makes a
findings list worthless. If you cannot name the component, the count or the file, do
not write it.

**Structure only, and say so.** The scan sees decorators, templates and injections,
never a running app. A change detection problem, a memory leak, a slow list - those
are suspicions. Write them as what they are ("a subscription in `ngOnInit` with no
`takeUntilDestroyed`") and let the reader confirm it.

## Name the rule, when the workspace has one

If the workspace carries a written rule set with ids - an ESLint config, Nx tags, a
conventions doc, a CONTRIBUTING - say which rule a finding breaks and use that id. It
goes into `detail`, never into `evidence`, which stays code:

> `LAYER-7`: Die ui-Komponente injiziert den State-Service; unterhalb der Page sollte
> nichts mehr injizieren.

Two things that buys: the finding and the workspace's own review vocabulary become
greppable as one, and an id is a claim you have to be able to back. It stays a
pointer, not a review - the scan sees decorators, templates and injections, whether
the rule is really broken is decided with the file open.

No such rule set? Then nothing is missing. Every pattern below is written to stand on
its own, and none of them needs an id to be a finding.

## How many, and when

| stage | at least | what makes them visible |
|---|---|---|
| 1 | none | names and stereotypes carry too little to say anything |
| 2 | 3 | inputs, outputs, signals, methods - size and shape |
| 3 | 5 | the edges - who injects whom, which library reaches where |
| 4 | 8 | the journeys - what a click actually sets off |

The counts are cumulative: what was found at stage 2 stays in the model, and every
later stage adds to it. They apply to a real codebase - below roughly 25 classes in
the model they are an orientation and the validator stops asking, because eight
findings about fifteen classes are padding by definition. They are a floor, not a
target - a workspace that hands you twelve at stage 3 gets twelve. Falling below it
happens, and then the report says which stage found nothing and why, rather than the
model carrying padding.

## Categories

| category | for |
|---|---|
| `size` | a component, template or state service grown past what one head holds |
| `coupling` | too many injections, a state service everything depends on |
| `boundary` | an Nx boundary crossed, a deep import past a barrel |
| `layering` | a ui component reaching into state, a page talking to the api directly |
| `state` | state kept in two places, a signal nobody reads, mutation from outside |
| `template` | logic in the template, no `@if`/`@for`, a template past what fits on a screen |
| `reactivity` | a subscription without teardown, an `effect()` that writes a signal, manual `detectChanges` |
| `typing` | `any` at the api boundary, a response type that does not match the backend |
| `authorization` | a guard that is not there: a route without the `CanActivateFn` its siblings have, two routes on the same resource that disagree about who may open them, a request that leaves without the auth interceptor |
| `duplication` | two components doing the same thing in two libraries |
| `dead-code` | an output nobody binds, a route nothing links to |
| `naming` | a selector or a name that says something different from what it does |

## Severity

| severity | means |
|---|---|
| `high` | it breaks a rule the workspace set itself (an Nx tag boundary, the state layering), or it can show a user the wrong data |
| `medium` | it costs time on every change that touches it |
| `low` | consistency and readability - worth knowing, nobody drops a sprint for it |

Most findings are `medium`. If everything is `high`, nothing is.

---

## Stage 2 - what members and signals show

**1. A component past roughly 300 lines of TypeScript**, or a template past roughly
150 lines. Evidence: both counts, since the split is usually along the template.

**2. A component with more than about 10 `input()`s.** It is configured, not used -
and every call site has to know all ten. Two or three groups in those names are the
components it wants to be.

**3. A state service with more than about 15 exposed signals and resources.** Two
domains in one store. Look at which signals are read together.

**4. A component that injects more than about 5 services.** Especially a mix of
state and api services - it is doing the orchestration a page should do.

**5. An `input()` that is written to from inside the component.** The parent owns
that value and does not know it changed. `model()` says so explicitly, plain `input()`
does not.

**6. `changeDetection: OnPush` written out**, on Angular v22 or newer where it is
the default - the line says nothing and outlives the reason it was added. Read the
Angular major out of `package.json` before writing this one: below v22 the finding
inverts into its original form, a component *without* `OnPush` in a workspace where
everything else has it. Name the ratio either way - "4 of 61 components".

**7. `any` at the api boundary**, or an http call without a response type. The
contract with the backend is a guess from there on.

**8. Two components with nearly the same inputs and template shape** in two
libraries. One of them is the copy that stopped being maintained.

**9. A subscription without `takeUntilDestroyed` or an `async` pipe.** Every
navigation leaves one behind.

**10. Business rules in the template** - a chain of conditions in an `@if`, a
calculation in an interpolation. It cannot be tested and it runs on every check.

**11. APIs a newer Angular replaced, counted across the workspace.** Each one is a
grep and the ratio is the finding, so they belong in one entry per kind rather than
one per file: `@Input()`, `@Output()`, `@ViewChild()` or `EventEmitter` where the
signal equivalents exist; `*ngIf` / `*ngFor` / `*ngSwitch` instead of the native
control flow; `ngClass` / `ngStyle`; an inline `template:` in a workspace that
otherwise keeps templates in their own file. "9 of 74 components still on `@Input()`"
is a migration status somebody can act on - a list of nine file names is not. A
`@for` without `track` goes here too, and that one is `high`: the list rebuilds every
node on every change.

**12. An `effect()` that calls `.set()` or `.update()`.** It is a `computed()` or a
`linkedSignal()` written the expensive way, and it keeps two signals in sync until the
day the order of the writes changes. Name the component and the two signals. Not the
legitimate use - pushing a value *out* of Angular into localStorage, a chart library,
a logger - which writes to nothing that is a signal.

## Stage 3 - what the edges show

**13. A ui component that injects a state service.** The ui layer is supposed to
work off inputs alone; from here on it only works inside that one feature.

**14. A page that injects an api service directly**, skipping the state layer that
every other page goes through. Whatever the state layer caches or guards does not
apply here.

**15. A deep import past a barrel** - `@acme/orders/src/lib/internal/thing` instead
of `@acme/orders`. The library's public surface stopped meaning anything.

**16. An edge between two projects that the Nx graph does not have**, or one that
the tags forbid (`scope:a` reaching into `scope:b`). Name both tags.

**17. A state service injected by more than about 8 components.** Changing it is a
workspace-wide event.

**18. A cycle between two libraries**, or two state services calling each other.

**19. An `output()` nobody binds, or a route nothing navigates to.** One side was
deleted and the other stayed.

## Stage 4 - what the journeys show

**20. A journey where the same data is loaded twice** on one path - once by a
resolver and once by the page, or by two components that both ask the state service.

**21. A write journey with no optimistic update and no loading state**, in a
workspace where comparable journeys have one. The user gets a frozen screen.

**22. A journey crossing three or more projects.** One click, three owners.

**23. A route that loads protected data with no guard on it**, next to sibling routes
that have one. The contrast is the finding, so name both routes. `authorization`,
usually `high`.

**24. A form submit that talks to the api service directly**, bypassing the state
service that holds the same data - after it, the screen and the store disagree.

**25. A journey whose flow has one step.** All of it lives in the component.

**26. A request that leaves without the interceptor every other request goes
through.** A bare `fetch()`, a second `HttpClient` instance configured elsewhere, a
call made before the interceptor is registered. Only visible because the interceptor
step is repeated in every journey it applies to (`extraction.md`, section 5). Name
the call and what the interceptor adds that it misses - a token, a tenant header,
error handling. `authorization`.

**27. Two routes on the same resource that disagree about who may open them.** A
guard on the detail route and none on the edit route, a role that may cancel but not
edit, one `canMatch` where the neighbour has `canActivate`. Name both paths.
`authorization`.

---

## What it looks like in the model

Findings live at the top level, next to `flows`, and every one of them anchors to
something the picture already shows:

```jsonc
{
  "id": "f3",
  "title": "OrderListPage hält 610 Zeilen und vier injizierte Services",
  "severity": "medium",
  "category": "size",
  "stage": 2,
  "nodes": ["OrderListPage"],
  "evidence": "610 lines ts, 220 lines html, injects OrderState, FilterState, OrderApi, ExportApi",
  "detail": "Die Seite hält Liste, Filterleiste und Export in einer Komponente. Der Export spricht als einziger Pfad direkt mit der API.",
  "suggestion": "Filterleiste und Exportdialog als Organismen herauslösen, den Export über OrderState führen."
}
```

`title`, `detail` and `suggestion` are written in the model language, the same as
every other text in the file. `evidence` carries counts and identifiers from the code
and stays as it is.

Every finding needs at least one `nodes` or `modules` entry. A finding that anchors
to nothing cannot be shown next to anything, and it is usually the sign of a finding
that was not concrete enough to begin with.
