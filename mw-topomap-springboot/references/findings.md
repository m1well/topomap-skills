# Findings - what to write down while reading

A scan reads more of the codebase in an afternoon than most people read in a quarter,
and everything it notices on the way is thrown away the moment the model is written.
`findings` is where that goes: the things that stood out, with the number that made
them stand out.

**A finding is an observation, not advice.** "The service has 19 constructor
parameters" is a finding. "Consider splitting large services" is a fortune cookie -
it would be true without ever having opened the repo, and it is exactly what makes a
findings list worthless. If you cannot name the class, the count or the file, do not
write it.

**Structure only, and say so.** The scan sees declarations and call edges, never a
running system. An N+1 query, a slow endpoint, a race condition - those are
suspicions. Write them as what they are ("a `@OneToMany` without a fetch strategy on
an entity that is loaded in a list endpoint") and let the reader confirm it.

## How many, and when

| stage | at least | what makes them visible |
|---|---|---|
| 1 | none | names and stereotypes carry too little to say anything |
| 2 | 3 | members, signatures, entity columns - size and shape |
| 3 | 5 | the edges - coupling, layering, module boundaries |
| 4 | 8 | the flows - order, guards, transaction boundaries |

The counts are cumulative: what was found at stage 2 stays in the model, and every
later stage adds to it. They apply to a real codebase - below roughly 25 classes in
the model they are an orientation and the validator stops asking, because eight
findings about fifteen classes are padding by definition. They are a floor, not a
target - a repo that hands you twelve at stage 3 gets twelve. Falling below it
happens, and then the report says which stage found nothing and why, rather than the
model carrying padding.

The stages differ in what they *can* see, which is why the number grows on its own:
stage 2 sees one class at a time, stage 3 sees how they hang together, stage 4 sees
what actually happens on a request.

## Categories

| category | for |
|---|---|
| `size` | a class, method, entity or repository grown past what one head holds |
| `coupling` | too many dependencies in or out, hub classes, cycles |
| `boundary` | a module boundary that leaks, an internal reached past its facade |
| `layering` | a layer skipped - controller straight to repository, entity in a response |
| `persistence` | schema and mapping: missing key, fetch strategy, enum as free text |
| `transaction` | transaction scope, network calls under a lock, missing atomicity |
| `api` | inconsistent endpoints, no facade, a module with no public surface |
| `authorization` | a guard that is not there: no permission or tenant check on a path whose siblings have one, two endpoints on the same resource that disagree about who may call them, a role that reaches further than the neighbouring endpoint allows |
| `duplication` | two classes that do the same thing in two places |
| `error-handling` | a swallowed error path, a listener without a failure route |
| `dead-code` | an event nobody listens to, an endpoint nothing reaches |
| `naming` | a name that says something different from what the class does |

## Severity

| severity | means |
|---|---|
| `high` | it breaks a rule the project set itself (a module boundary, a layer), or it can lose or corrupt data |
| `medium` | it costs time on every change that touches it |
| `low` | consistency and readability - worth knowing, nobody drops a sprint for it |

Most findings are `medium`. If everything is `high`, nothing is.

---

## Stage 2 - what members and columns show

**1. A class past roughly 400 lines, or with more than about 15 public methods.**
It does more than one thing. Evidence: the line count and the method count.

**2. A constructor with more than about 10 dependencies.** The number *is* the
finding - a class that needs 19 collaborators has at least three jobs. Put the count
in `tags` on the node too, so it shows on the card.

**3. An entity with more than about 25 columns.** Usually two or three concepts in
one table. Look for column name prefixes - `versand_*`, `rechnung_*` groups are the
seam it would split along.

**4. An entity without a primary key, or without the audit base class its siblings
have.** Either the extraction missed the `@MappedSuperclass` (then fix the model) or
this table really is different from the other forty (then it is a finding).

**5. A repository with more than about 20 query methods.** The business logic moved
into derived query names. Related: a repository with `@Query` blocks longer than a
few lines - that is a view waiting to be named.

**6. A method with more than about 6 parameters**, especially several of the same
type next to each other. Two `UUID`s in a row is a call site waiting to swap them.

**7. A controller method that returns an entity instead of a DTO.** The persistence
model is the API contract now, and the next column rename is a breaking change.

**8. An enum-like column mapped as plain text without `@Enumerated`**, or a status
kept as `String`. Every value check is a string comparison.

**9. Two classes with near-identical member lists.** `*ReadService` and
`*QueryService` in different modules, same five methods - one of them is a copy that
stopped being maintained.

**10. A `@Scheduled` job with no visible lock or guard.** Fine on one instance, a
double execution as soon as there are two. Say which it is if the deployment tells
you.

## Stage 3 - what the edges show

**11. A controller with an edge straight to a repository.** The service layer got
skipped, so whatever the service guarantees does not happen on this path.

**12. A module every other module reaches into, with no `api` class.** Name the
classes that are imported from outside - that list is the facade the module never
got.

**13. A cross-module edge without a build dependency behind it.** Three shapes are
allowed (see `extraction.md`, section 6); everything else is a finding, and the
interesting one is the interface-in-shared-module case that an architecture test
cannot see because only the shared module is on its classpath.

**14. A cycle** - two modules that depend on each other, or two services that call
each other. Name both directions with their labels.

**15. A hub: more than about 12 outgoing edges from one class, or more than about 10
incoming.** Outgoing is an orchestrator that grew; incoming is a class nobody can
change any more.

**16. An entity written from more than one module.** No owner, so no invariant
either. Name the writing modules.

**17. An event with no listener, or a listener whose event nobody publishes.** One
of the two sides was deleted and the other stayed.

**18. A call to an external system with no timeout, no retry and no fallback in the
calling class.** Visible as soon as the `external` node exists: follow the `http`
edge back and read the client. The other system's bad day becomes yours - and if the
call sits inside a request path, its latency is your endpoint's latency. Name the
system and the calling class.

## Stage 4 - what the flows show

**19. A write flow with no guard on it.** No permission check, no tenant check, no
state check between the endpoint and the insert. Compare against a sibling flow that
does have one - that contrast is the finding. `authorization`.

**20. Two flows over the same edges in a different order.** One of them is right.
Name both and the step where they diverge.

**21. A flow crossing three or more modules.** One request, three owners, and a
change to it needs three reviews. Worth naming even when nothing is wrong with it.

**22. An outbound HTTP or queue call inside a transaction.** The transaction stays
open for as long as the other system takes. Visible in the model when a `http` edge
sits between two `call` edges of a transactional service.

**23. A write flow that publishes no event while comparable flows do.** Whoever
listens for the others silently misses this one.

**24. An endpoint whose flow has one step.** All of it lives in the controller.

**25. An endpoint that does not pass through the filter chain its siblings pass
through.** Four of thirty-six flows starting at the controller while the other
thirty-two start at the `AuthTokenFilter` is not a modelling detail, it is the
question the diagram was opened for. Only visible because the guard step is repeated
in every flow it applies to (`extraction.md`, section 5). Name the four and say what
the filter does that they miss. `authorization`, usually `high`.

**26. Two endpoints on the same resource that disagree about who may call them.** A
role that may cancel the race but not touch its stint plan, one `@PreAuthorize` where
the neighbour has none, a tenant check on the read and not on the write. The finding
is the contrast between the two paths, so name both. `authorization`.

---

## What it looks like in the model

Findings live at the top level, next to `flows`, and every one of them anchors to
something the picture already shows:

```jsonc
{
  "id": "f3",
  "title": "CreateErfassungsergebnisService trägt 19 Abhängigkeiten",
  "severity": "medium",
  "category": "coupling",
  "stage": 2,
  "nodes": ["CreateErfassungsergebnisService"],
  "evidence": "19 constructor parameters, 640 lines, 11 public methods",
  "detail": "Der Service hält Erfassung, Heilverlauf und Diagnosestellung in einer Klasse. Jede der drei Aufgaben zieht ihre eigenen vier bis sieben Mitspieler mit.",
  "suggestion": "Entlang der drei Aufgaben schneiden - die Abhängigkeiten gruppieren sich bereits so."
}
```

`title`, `detail` and `suggestion` are written in the model language, the same as
every other text in the file. `evidence` carries counts and identifiers from the
code and stays as it is.

Every finding needs at least one `nodes` or `modules` entry. A finding that anchors
to nothing cannot be shown next to anything, and it is usually the sign of a finding
that was not concrete enough to begin with.
