# Extracting the model from an Angular workspace

Every recipe is a starting point for finding files - read the file before you put
anything in the model. Never derive an edge from a grep hit alone.

## 0. Count before you ask about scope

The scope question has to carry numbers - "one product or the whole workspace?"
means nothing until both have a size. One call fills them in:

```bash
for p in $(find . \( -name project.json -o -name ng-package.json \) -not -path '*/node_modules/*' | sed 's|/[^/]*$||' | sort -u); do
  src="$p/src"; [ -d "$src" ] || src="$p"
  printf '%-38s files=%-4s comp=%-4s inj=%-3s routes=%s\n' "${p#./}" \
    "$(find $src -name '*.ts' -not -name '*.spec.ts' 2>/dev/null | wc -l | tr -d ' ')" \
    "$(grep -rl '@Component' $src --include='*.ts' 2>/dev/null | wc -l | tr -d ' ')" \
    "$(grep -rl '@Injectable' $src --include='*.ts' 2>/dev/null | wc -l | tr -d ' ')" \
    "$(grep -rhoE '[[:space:]{,]path:' $src --include='*.ts' 2>/dev/null | wc -l | tr -d ' ')"
done
```

The route count is the size of stage 4 before it is written; the component count per
project is the cut line to offer. **Quote the globs** - `--include=*.ts` unquoted
makes zsh answer `no matches found` before grep is started, and BSD grep on macOS
does not know `\s`, so character classes it is.

## 1. Projects

**Nx** - the graph is a command away, and it is the authoritative answer:

```bash
npx nx graph --file=/tmp/graph.json   # nodes + dependencies, no guessing
python3 -c "
import json; g=json.load(open('/tmp/graph.json'))['graph']
for name, deps in g['dependencies'].items():
    own=[d['target'] for d in deps if not d['target'].startswith('npm:')]
    print(name, '->', ' '.join(own) or '-')"
```

If the command is not available (no install, CI-less checkout), fall back to the
static sources:

```bash
rg -n '"name"|"tags"|"sourceRoot"' --glob '**/project.json' --glob '!**/node_modules/**'
python3 -c "
import json,re; s=re.sub(r'//.*','',open('tsconfig.base.json').read())
[print(k,'->',v[0]) for k,v in json.load(s and __import__('io').StringIO(s) or None)['compilerOptions']['paths'].items()]" 2>/dev/null \
  || rg -n '@[a-z0-9-]+/' tsconfig.base.json
```

The `paths` map is the important one: it lists every library alias and the barrel
file behind it. Imports between libraries always go through those aliases, so the
alias is what you grep for when looking for cross-project edges.

**Nx tags** (`"tags": ["scope:erfassera", "type:feature"]` in `project.json`) tell
you what a library is allowed to depend on. Put them in the module's `description`
- a lane that says `scope:shared · type:ui` explains itself.

**Classic workspace** - `angular.json` / `workspace.json` `projects` block. A
single-app project becomes one lane and the layer columns still carry the picture -
until that lane passes roughly 40 cards, at which point the feature folders under
`src/app/` become the lanes instead. Say in the report that they are folders, not
projects: nothing enforces a folder boundary, so an edge across one is an observation
and not a violation.

**Not a lane:** e2e projects, tooling, generators, anything under `tools/`.

## 2. Classes by stereotype

**Decorators first - file names lie.** Modern Angular has no `.component.ts`
suffix any more, so `sortier-wahl.ts` can be anything:

```bash
rg -l '@Component'  --glob '**/*.ts' --glob '!**/node_modules/**' --glob '!**/*.spec.ts'
rg -l '@Injectable' --glob '**/*.ts' --glob '!**/node_modules/**' --glob '!**/*.spec.ts'
rg -l '@Directive|@Pipe' --glob '**/*.ts' --glob '!**/node_modules/**'
rg -n 'Routes\s*=|CanActivateFn|CanMatchFn|ResolveFn|HttpInterceptorFn' --glob '**/*.ts' --glob '!**/node_modules/**'
```

**Then the directory decides the layer.** Atomic-design folders are the strongest
signal in a workspace that uses them:

| path contains | stereotype |
|---|---|
| `/pages/`, `/seiten/` | `page` |
| `/organisms/` | `organism` |
| `/templates/` | `template` |
| `/molecules/` | `molecule` |
| `/atoms/` | `atom` |
| `/state/` | `state` |
| `/data/`, `/data-access/` | `api` |
| `/model/`, `/models/` | `model` |
| `/directives/` | `directive` |
| `/pipes/` | `pipe` |

**Then file prefixes**, for flat libraries that do not nest by layer:
`api-*.ts` → `api`, `state-*.ts` / `store-*.ts` → `state`.

**A component that is a route target is a `page`**, wherever it sits - check the
route files before assigning `organism`.

**Telling the two `@Injectable` kinds apart:** a service holding `signal()`,
`computed()`, `linkedSignal()`, `rxResource()` or `httpResource()` is `state`; a
service whose methods are `HttpClient` calls is `api`. A service that does both is
a finding worth reporting, not a stereotype - name it `state` and say so.

```bash
rg -l 'rxResource|httpResource|signal\(|computed\(' path/to/lib
rg -l 'HttpClient|inject\(HttpClient\)' path/to/lib
```

**In the diagram:** routes, guards, resolvers, interceptors, pages, organisms,
state services, api services, models that matter, plus the ui pieces used across
project boundaries.

**Not in the diagram:** spec files, storybook files, generated code, barrel files,
`environment.ts`, pure helper functions, and ui atoms used everywhere - a button
in forty places is noise on every lane.

## Stereotypes and edge kinds

| stereotype | column | use for |
|---|---|---|
| `route` | 0 Route | a `Routes` array |
| `guard` | 0 Route | `CanActivateFn`, `CanMatchFn` |
| `resolver` | 0 Route | `ResolveFn` |
| `page` | 1 Page | a component a route points at |
| `organism` | 2 Organism | a feature component that composes others |
| `template` | 2 Organism | a layout shell others fill |
| `molecule` | 3 UI | a reusable piece with a little logic |
| `atom` | 3 UI | a leaf component |
| `directive` | 3 UI | `@Directive` |
| `pipe` | 3 UI | `@Pipe` |
| `state` / `store` | 4 State | an `@Injectable` holding signals and resources |
| `api` | 5 Data | an `@Injectable` calling `HttpClient` |
| `model` | 5 Data | the types that travel over the wire |
| `interceptor` | 5 Data | `HttpInterceptorFn` |
| `client` | 5 Data | the backend itself - one node, not one per endpoint |
| `component` | 2 Organism | fallback when nothing else fits |

Override the column of a single node with `rank` without changing its stereotype -
that is how shared ui pieces land in the UI column instead of next to the feature
organisms.

| kind      | line          | use for                                        |
|-----------|---------------|------------------------------------------------|
| `call`    | solid         | direct method call, constructor injection      |
| `http`    | solid         | outbound HTTP to another system                |
| `event`   | dotted        | publish / listen, no direct call               |
| `persist` | dashed        | repository to entity, entity to child entity   |
| `maps`    | dashed        | mapper converting between two types            |

## 3. Members

**Components** - the signal API, not the class body:

```bash
rg -n '= input(\.required)?<|= output<|= model<|= viewChild' path/to/component.ts
rg -n '^\s*(protected |public )?[a-zA-Z]+\(' path/to/component.ts   # methods a template calls
```

Take `input()` / `output()` / `model()` with their types - they are the contract of
the component, the same way a signature is for a service. Skip lifecycle hooks
unless they carry logic worth a line.

**State services** - what they expose and what mutates it:

```bash
rg -n '= (signal|computed|linkedSignal|rxResource|httpResource)' path/to/state.ts
rg -n '^\s*(readonly )?[a-zA-Z]+\s*[=(]' path/to/state.ts
```

A `rxResource` is worth its own member line: name, what it loads, and what it
depends on - that dependency is why it reloads.

**Api services** - one line per endpoint, and put the HTTP route in the `http`
field so it shows up like a controller mapping in the Spring variant.

**Routes** - the path and the component behind it:

```bash
rg -n -A3 "path:" path/to/feature.routes.ts
```

Lazy routes (`loadComponent`, `loadChildren`) are edges to another project - note
them, they are the seam between the app shell and a feature library.

## 4. Edges

**Injection** is the main source:

```bash
rg -n 'inject\(\w+\)' path/to/class.ts
rg -n -A6 'constructor\(' path/to/class.ts
```

**Template bindings are edges too**, and they are the ones people miss. A parent
uses a child through its selector, so grep the templates for it:

```bash
rg -n 'selector:' path/to/child.ts          # find the selector
rg -l '<app-wochen-tabelle' --glob '**/*.html'   # find the parents
```

The edge goes parent → child, `kind: "call"`, label from the parent's point of
view ("zeigt die Wochenzeilen"). An `output()` going back up is a second edge with
`kind: "event"` and the label of what it reports ("meldet den geänderten Filter").

**Routing** is a configuration edge: route file → component, `kind: "config"`,
label = the path. For `loadComponent` / `loadChildren` say that it is lazy.

**HTTP** leaves the process: api service → a `client` node standing for the
backend, `kind: "http"`, label = the endpoint. One node per backend is enough -
do not draw a box per endpoint.

**One node per *system*, though, not one for "the backend".** An app that talks to
its own api, to an identity provider and to an analytics endpoint has three of them,
and telling them apart is the point: the arrow into the identity provider is the one
someone opens the diagram to find. They live in a lane of their own at the end
(`modules` entry `id: "external"`, name `external systems`), because every node needs
a module and none of them belongs to a project in the workspace.

Do not draw an edge you only assume. If you cannot find the parent of a component,
leave it out and say so in the report.

## 5. User journeys

**Inventory first:**

```bash
rg -n "path:\s*'" --glob '**/*.routes.ts' --glob '**/*.ts' --glob '!**/node_modules/**'
rg -n '\(click\)=|\(submit\)=|\(ngSubmit\)=' --glob '**/*.html'
```

Every route is a journey - someone navigates there and something loads. Every
state-changing command is a journey - someone clicks and something is written.
That is the candidate list; the default is one flow each.

A read journey usually runs route → page → state → api → backend, and back into
the organisms that render it. A write journey runs organism → state → api →
backend and then re-triggers the resource that reloads the list. **That reload is
the step people never see in the code** - if a `rxResource` re-runs because a
signal it depends on changed, say so in the step note.

**A step that repeats in nearly every journey still goes into every journey.** An
`authInterceptor` on every outgoing request, an `errorInterceptor` on every response,
a `CanActivateFn` on every route under `/admin` - the renderer only ever shows one
flow at a time, so a flow has to tell the truth about *that* click on its own. Leave
the interceptor out and the picture says the api service talks to the backend
directly, which is the thing someone opened the diagram to check.

The repetition pays for itself: the journeys *without* the guard are only visible as
an exception because the others carry it, and that contrast is a finding
(`findings.md`, stage 4, patterns 21 and 24) that cannot be seen any other way.

Merge only what is literally the same chain. Say in the report what you dropped.

## 6. Sanity check before you build

- `"preset": "angular"` is set in `meta`
- every `node.module` exists in `modules`, every edge endpoint exists in `nodes`
- every flow step resolves to an edge, steps in execution order
- no cross-project edge without a dependency in the Nx graph behind it
- components carry their inputs and outputs, api services their routes, state
  services their signals and resources
- the model is valid json

After building, open the diagram and read the "model issues" box in the panel.
