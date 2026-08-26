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
| `reactivity` | a subscription without teardown, no OnPush, manual `detectChanges` |
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

**6. A component with no `changeDetection: OnPush`** in a workspace where everything
else has it. Name the ratio - "4 of 61 components".

**7. `any` at the api boundary**, or an http call without a response type. The
contract with the backend is a guess from there on.

**8. Two components with nearly the same inputs and template shape** in two
libraries. One of them is the copy that stopped being maintained.

**9. A subscription without `takeUntilDestroyed` or an `async` pipe.** Every
navigation leaves one behind.

**10. Business rules in the template** - a chain of conditions in an `@if`, a
calculation in an interpolation. It cannot be tested and it runs on every check.

## Stage 3 - what the edges show

**11. A ui component that injects a state service.** The ui layer is supposed to
work off inputs alone; from here on it only works inside that one feature.

**12. A page that injects an api service directly**, skipping the state layer that
every other page goes through. Whatever the state layer caches or guards does not
apply here.

**13. A deep import past a barrel** - `@acme/orders/src/lib/internal/thing` instead
of `@acme/orders`. The library's public surface stopped meaning anything.

**14. An edge between two projects that the Nx graph does not have**, or one that
the tags forbid (`scope:a` reaching into `scope:b`). Name both tags.

**15. A state service injected by more than about 8 components.** Changing it is a
workspace-wide event.

**16. A cycle between two libraries**, or two state services calling each other.

**17. An `output()` nobody binds, or a route nothing navigates to.** One side was
deleted and the other stayed.

## Stage 4 - what the journeys show

**18. A journey where the same data is loaded twice** on one path - once by a
resolver and once by the page, or by two components that both ask the state service.

**19. A write journey with no optimistic update and no loading state**, in a
workspace where comparable journeys have one. The user gets a frozen screen.

**20. A journey crossing three or more projects.** One click, three owners.

**21. A route that loads protected data with no guard on it**, next to sibling routes
that have one. The contrast is the finding, so name both routes. `authorization`,
usually `high`.

**22. A form submit that talks to the api service directly**, bypassing the state
service that holds the same data - after it, the screen and the store disagree.

**23. A journey whose flow has one step.** All of it lives in the component.

**24. A request that leaves without the interceptor every other request goes
through.** A bare `fetch()`, a second `HttpClient` instance configured elsewhere, a
call made before the interceptor is registered. Only visible because the interceptor
step is repeated in every journey it applies to (`extraction.md`, section 5). Name
the call and what the interceptor adds that it misses - a token, a tenant header,
error handling. `authorization`.

**25. Two routes on the same resource that disagree about who may open them.** A
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
