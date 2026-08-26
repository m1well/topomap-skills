# Extracting the model from a Spring Boot repo

Kotlin or Java, Gradle or Maven - the model is the same either way, and so is the
renderer. Only the recipes below differ. Substitute `**/*.java` for `**/*.kt`
wherever the language matters; the Spring annotations are identical in both.

Every recipe is a starting point for **finding** files. **Reading** them out is the
job of the three extractors in `$SKILL/assets/extract/` (`SKILL` is set in
`SKILL.md`) - a Kotlin primary constructor runs
over as many lines as it has parameters, and the class with nineteen of them is
exactly the one whose edges must not be half missing. Never derive an edge from a
grep hit alone, and never count on `-A6` catching the whole declaration.

Two shell traps that cost real time on a first run:

- **Quote your globs.** `--include=*.kt` makes zsh answer `no matches found` before
  grep is even started. Always `--include='*.kt'`. The `rg --glob '**/*.kt'` recipes
  below are quoted correctly.
- **Half the Spring annotations are the prefix of another one.** A search for
  `@Entity` finds `@EntityScan` on the bootstrap class, `@Controller` finds
  `@ControllerAdvice`, `@Component` finds `@ComponentScan`. A `^` anchor does not
  save you: `@EntityScan` and `@ComponentScan` sit at column 0 exactly like the real
  thing. So say where the name ends - `\b` in rg, `([^A-Za-z]|$)` in grep, because
  `\b` is not POSIX and a grep that reads it as a literal `b` returns a silent zero:

  | searching for | also matches |
  |---|---|
  | `@Entity` | `@EntityScan`, `@EntityGraph`, `@EntityListeners`, `@EntityResult` |
  | `@Controller` / `@RestController` | `@ControllerAdvice`, `@RestControllerAdvice` |
  | `@Component` | `@ComponentScan`, `@ComponentScans` |
  | `@Repository` | `@RepositoryDefinition`, `@RepositoryRestResource` |
  | `@Service` | `@ServiceActivator` |
  | `@Configuration` | `@ConfigurationProperties` |

  The advice classes are worth knowing about, they are just not controllers - a
  global exception handler is an error path and stays out, so counting it as one
  inflates the number the scope question is built on.

## 0. Count before you ask about scope

The scope question has to carry numbers, otherwise the options are empty claims.
One call fills them in:

```bash
for m in $(find . -type d -path '*/src/main' -not -path '*/node_modules/*' | sed 's|/src/main||' | sort); do
  printf '%-28s files=%-4s ctrl=%-3s svc=%-3s repo=%-3s entity=%-3s endpoints=%s\n' "${m#./}" \
    "$(find $m/src/main \( -name '*.kt' -o -name '*.java' \) | wc -l | tr -d ' ')" \
    "$(grep -rlE '@RestController([^A-Za-z]|$)' $m/src/main --include='*.kt' --include='*.java' 2>/dev/null | wc -l | tr -d ' ')" \
    "$(grep -rlE '@Service([^A-Za-z]|$)' $m/src/main --include='*.kt' --include='*.java' 2>/dev/null | wc -l | tr -d ' ')" \
    "$(grep -rlE 'JpaRepository|@Repository([^A-Za-z]|$)' $m/src/main --include='*.kt' --include='*.java' 2>/dev/null | wc -l | tr -d ' ')" \
    "$(grep -rlE '^@Entity([^A-Za-z]|$)' $m/src/main --include='*.kt' --include='*.java' 2>/dev/null | wc -l | tr -d ' ')" \
    "$(grep -rhoE '@(Get|Post|Put|Patch|Delete|Request)Mapping' $m/src/main --include='*.kt' --include='*.java' 2>/dev/null | wc -l | tr -d ' ')"
done
```

The endpoint count is the size of stage 4 before it is written, and the class counts
per module are the cut lines to offer.

## 1. Modules

**Gradle**

```bash
rg -N 'include' settings.gradle.kts settings.gradle
rg -n 'project\(["'"'"']:' --glob '**/build.gradle*'   # dependencies between modules
```

**Maven**

```bash
rg -n -A30 '<modules>' pom.xml | rg '<module>'        # the module list
rg -n -B2 -A4 '<artifactId>' */pom.xml | rg -A3 '<dependency>'
```

In Maven a dependency is a module dependency when its `groupId` is the project's
own (often `${project.groupId}`) - everything else is a third party library and
does not belong in the diagram. A single-module Maven or Gradle project is fine
too: it becomes one lane, and the layer columns still carry the picture.

Either way you now have the allowed module graph. Note it down - it is the guard
rail for step 6. A class edge that crosses a boundary the build graph does not
have is either wrong, one of the three allowed shapes, or a finding worth
reporting.

Modules that only carry plugins, versions, BOMs or test fixtures do not become
lanes.

## 2. Classes by stereotype

```bash
rg -l '@(Rest)?Controller\b'             --glob '**/*.kt'
rg -l '@Service\b'                       --glob '**/*.kt'
rg -l '@Repository\b|: *(Jpa|CrudRepository|PagingAndSorting)' --glob '**/*.kt'
rg -l '^@Entity\b|@Document\b|@Table\b' --glob '**/*.kt'
rg -l '@Component\b'                     --glob '**/*.kt'
rg -l '@FeignClient|RestClient|WebClient|RestTemplate' --glob '**/*.kt'
rg -l '@EventListener|@TransactionalEventListener|@KafkaListener|@RabbitListener' --glob '**/*.kt'
rg -l '@Scheduled'                       --glob '**/*.kt'
rg -l 'OncePerRequestFilter|HandlerInterceptor|WebMvcConfigurer|SecurityFilterChain|@PreAuthorize' --glob '**/*.kt'
```

That last line is the `guard` row further down, and it is the one an annotation sweep
misses: a `Filter` carries no Spring annotation at all, it is registered in a config
class. Nearly every Spring Boot app has two or three, and they run before every
request in the app.

Module api classes rarely carry an annotation. Find them by name and by position:
`*Facade`, `*Api`, `*Gateway`, or the one public class in a module whose internals
live in an `internal` package. Cross-check with what other modules actually import.

### What you can drop without opening the file

Names are not proof, but these carry business logic so rarely that opening them all
is not worth the time:

| pattern | why not |
|---|---|
| `*Dto`, `*RequestDto`, `*ResponseDto` | transport format, never a node |
| `*Command`, `*Result` | facade parameters - they belong in the facade's summary |
| `*Event` | the edge is the node, not the event type |
| `*Properties`, `*ConfigData` | `@ConfigurationProperties` holders |
| `*Configuration` | bean wiring |
| `*Exception` | an error path - it belongs in the method's `doc` |
| `*Converter` | JPA `AttributeConverter`, pure type mapping |
| `*Embeddable` | part of the entity, appears as a column |
| `*Specifications` | Specification builders, usually a Kotlin `object` |
| `*Seeds`, `*Matrix`, `*Registry` | static data tables that happen to live in code |
| `*Utils`, `*Util`, `*Helper`, `*Constants` | see the counter-check below |
| `*Fake*`, `*Stub*`, `*Test*` | test doubles |

**Structure beats the name.** Three signals that hold better than any suffix:

- a **`data class`** is practically never a node
- a **`sealed interface` with `data object` variants** is a result type - out
- an **`object` without state** is a helper facade - out

### The three that look droppable and are not

This is where the suffix rule tips over, so check these before dropping anything:

- **The file name is not the class.** `CiDataService` can sit in `CiData.kt`. Decide
  by the class declaration and its annotation, never by the file name - a filter
  over `find -name '*Dto.kt'` loses that class.
- **Two neighbours, one name.** `MandantInitializerSeeds` is 600 lines of seed data
  and stays out; `MandantInitializer` is an `@EventListener(ApplicationStartedEvent)`
  and goes in.
- **A suffix nobody listed.** `*Parser` is on no list and can hold the decision the
  whole webhook path depends on. If a class appears in a flow step, it needs a node -
  otherwise that step has no edge and gets dropped.

### Name patterns that do earn a box

The annotation list above misses the classes a codebase names by convention:

| pattern | stereotype | typical |
|---|---|---|
| `*Adapter`, `*BackendAdapter` | `client` | outbound calls into another system |
| `*Job` | `job` | `@Scheduled` - an entry point like a controller |
| `*Writer`, `*Appender`, `*Applicator` | `service` | they change state |
| `*Processor`, `*Handler`, `*Resolver` | `service` | they decide something |
| `*Parser` | `service` | when it holds logic, not when it maps types |
| `*Dao`, `*DaoImpl` | `client` | when the infrastructure behind it is not JPA (JMS, files) |

**In the diagram:** controllers, module apis, services, repositories, entities,
clients, listeners, mappers, scheduled jobs.

**Not in the diagram:** utils, helpers, extension files, constants, exceptions,
DTOs and records, converters, `@Configuration` that only wires beans, anything
under `src/test`, and generated code. If a "helper" turns out to hold real business
rules, it goes in as a `service` - judge by content, not by the name.

### Interface and implementation

One box, not two - the implementation gets the box and the interface is named in its
summary. **Except when the interface is the module's public api**, which in a modular
codebase is the normal case: the `*Facade` interfaces live in the shared api module,
the `*FacadeImpl` classes in the modules that own them. Then:

- the interface is `stereotype: "api"`, the impl is `stereotype: "service"`
- cross-module edges point at the **interface**
- one edge `interface -> impl`, `kind: "call"`, label `implemented by`
- in a cross-module flow that edge is **a step of its own** - without it the flow
  jumps from the caller straight into the impl, an edge that does not exist, and
  the renderer drops the step

With several implementations, draw the edge to the interface and list the
implementations in its summary.

## Stereotypes and edge kinds

The stereotype decides colour, icon and which column the card lands in. Columns are
global across all lanes, so the layers line up between modules.

| stereotype   | column        | palette colour       | use for                                          |
|--------------|---------------|----------------------|--------------------------------------------------|
| `controller` | 0 Controller  | primary              | `@RestController`, `@Controller`                  |
| `job`        | 0 Controller  | primary + warning    | `@Scheduled` - a trigger, so it sits with the entry points |
| `api`        | 1 Module API  | secondary            | facade / public api class of a module             |
| `facade`     | 1 Module API  | secondary            | same, alias                                       |
| `service`    | 2 Service     | success              | `@Service`, use case classes                      |
| `usecase`    | 2 Service     | success              | same, alias                                       |
| `component`  | 2 Service     | gray                 | plain `@Component`, fallback for anything unknown |
| `mapper`     | 3 Integration | warning              | mapstruct or hand-written mappers                 |
| `client`     | 3 Integration | secondary + warning  | outbound HTTP / gRPC clients, `@FeignClient`      |
| `event`      | 3 Integration | primary + danger     | `@EventListener`, `@KafkaListener`, publishers    |
| `config`     | 3 Integration | gray                 | `@Configuration` worth showing                    |
| `repository` | 4 Repository  | danger               | `@Repository`, Spring Data interfaces             |
| `entity`     | 5 Domain      | info                 | `@Entity`, `@Document`, aggregates                |

The colour column is the MaverickWave palette entry the stereotype is bound to, so
a `meta.theme` override carries through to every card.

Use `rank` on a node to move a single card into another column without changing
its colour.

### Two more, declared in the model

The `spring` preset does not ship these, and both come up on every second Spring Boot
app. They are declared in `meta.stereotypes` - see `model-format.md` - and from then
on they behave like any other stereotype, filter row included:

```jsonc
"meta": {
  "stereotypes": {
    "guard":    { "label": "guard",    "rank": 0, "icon": "shield", "color": "var(--mw-warning-color)" },
    "external": { "label": "external", "rank": 5, "icon": "globe",  "color": "var(--mw-gray-color)" }
  }
}
```

**`guard` - what runs before the controller.** A `Filter`, a `HandlerInterceptor`,
an `@ControllerAdvice` that authorises rather than translating errors, a
`@PreAuthorize` aspect. They sit in front of the entry point in time, so they sit in
column 0 in the picture too, next to `job`. Giving them `service` puts them in
column 2 - behind the controller they run in front of, which is the one thing the
picture then states wrongly. In a flow the guard is **step 1**, before the controller
edge.

**`external` - the system on the other end.** The `http` edge kind exists, but
without a node there is nothing for it to point at, and the calls that leave the
process are the most interesting arrows in the diagram. So the other system gets a
card: `OpenRouter`, `Idently`, `Stripe`. One node per system, never one per endpoint.

- it goes in its own lane at the end, `modules` entry `id: "external"`, name
  `external systems`, path empty. Every node needs a module, and a lane of its own
  keeps it out of the build graph it is not part of
- the edge runs from the class that calls out - the `client`, the adapter, the
  service - to that node, `kind: "http"`, label = what it asks for ("asks the model
  to parse the bop table")
- rank 5 puts it at the far right, so the arrow reads left to right like every
  other one. The colour is deliberately grey: it is code you cannot change, and the
  arrow is the point, not the card
- an external system with no timeout, no retry and no fallback in the calling class
  is a finding worth writing down, and it is only visible once the node exists

**A class can be two things at once.** A `@RestController` that is also a
`@TransactionalEventListener` feeding an SSE stream is a common shape. Pick the
stereotype that says where it belongs in the picture, put the rest into `tags`, and
point the event edges at it:

```jsonc
{ "id": "OrderLiveController", "stereotype": "controller",
  "tags": ["SSE", "@TransactionalEventListener"] }
```

| kind      | line          | use for                                        |
|-----------|---------------|------------------------------------------------|
| `call`    | solid         | direct method call, constructor injection      |
| `http`    | solid         | outbound HTTP to another system                |
| `event`   | dotted        | publish / listen, no direct call               |
| `persist` | dashed        | repository to entity, entity to child entity   |
| `maps`    | dashed        | mapper converting between two types            |

## 3. Members

Find the files with `rg`, then read the signatures out with the extractor - it
follows the parentheses across line breaks, cuts Kotlin expression bodies, and does
not care whether the project indents with two spaces or four:

```bash
python3 $SKILL/assets/extract/funs.py path/to/Class.kt path/to/Other.kt
```

It leaves out everything private, protected or internal and
`equals`/`hashCode`/`toString`; Java bean accessors go too, Kotlin `getX()` methods
stay - on a service that is an ordinary method name, not an accessor. On an interface
it takes everything: on a Spring Data repository the derived query name *is* the
documentation.

**Read its stderr.** The extractor measures every file twice - once by parsing it,
once by counting the method declarations in the class body by brace depth - and says
so when the two disagree:

```
!! fewer signatures than declarations - the extraction lost methods here:
   AdminRaceService.kt: 2 printed, 4 lost - line(s) 12, 16, 21, 25
```

**Fewer methods than declarations in the file means the extraction failed, not that
the class has few methods** - the same rule the entity extractor has for zero
columns. Nothing downstream can catch it: `validate.py` sees a class with two methods
and has no way of knowing there were six, and stage 2 quietly ends up half written.
When it fires, open the file and read those lines by hand. A cheap counter-check on
any file you are unsure about:

```bash
grep -cE '^  (override |suspend )*fun ' path/to/Service.kt   # adjust the indent
```

Endpoints: the `http` field is the method plus the full path. Read the class level
`@RequestMapping` for the prefix.

```bash
rg -n '@(Get|Post|Put|Patch|Delete|Request)Mapping' path/to/Controller.kt
```

The `doc` line is yours to write. State the effect and the notable edge case, in
one line. Do not copy the KDoc, and do not restate the signature in prose.

## 4. Edges

**Constructor injection** is the main source. One call over every service at once:

```bash
python3 $SKILL/assets/extract/ctor.py $(rg -l '@Service\b|@Component\b' --glob '**/*.kt')
```

For Kotlin that is the primary constructor, counted out to its closing parenthesis.
For Java it prints all three shapes that occur: the constructor, the `private final`
fields behind Lombok's `@RequiredArgsConstructor`, and `@Autowired` field injection.

Every injected type that has its own node becomes an edge `from` this class `to`
that type. Injected types without a node (utils, config, `ObjectMapper`) are
skipped. A class with fifteen or more dependencies is worth a
`"tags": ["19 dependencies"]` - the badge puts the complexity on the card instead of
hiding it in the inspector.

**Events** have no call. Match the publish to the listener by event type:

```bash
rg -n 'publishEvent|ApplicationEventPublisher' --glob '**/*.kt'
rg -n '@EventListener|@TransactionalEventListener' -A3 --glob '**/*.kt'
```

The edge goes from the publishing class to the listening class, `kind: "event"`,
label `publishes CustomerCreated`.

**Persistence** edges: repository to its entity (`kind: "persist"`, label = table
name), plus entity to entity for `@OneToMany` / `@ManyToOne` (label = the
annotation).

### Entities

```bash
python3 $SKILL/assets/extract/entity.py $(rg -l '^@Entity\b' --glob '**/*.kt') > /tmp/entities.json
```

Three things the extractor reports and you have to finish by hand:

- **`supertypes`** - the audit columns are not in the entity file. `id`,
  `created_*`, `updated_*` and the soft-delete pair come from the
  `@MappedSuperclass` base. Read each base **once**, then prepend its columns to
  every entity that extends it. Skip this and half the tables have no primary key.
- **`inheritance: true`** - with `@Inheritance(JOINED)` the child table carries only
  its own columns plus the inherited `id`. Model the relation as an edge
  `child -> base`, `kind: "persist"`, label `@Inheritance JOINED`.
- **zero columns** - the extractor prints those to stderr. That is always an
  extraction failure, never an empty table: the properties sit in the class body in
  a shape the regex missed. Open the file.
- **`? SomeType`** - a Kotlin or Java type the extractor could not map to a db type,
  also on stderr. It is almost always an `@Converter(autoApply = true)`, an
  `@Embeddable`, or an enum with no `@Enumerated`. Read the converter for the type it
  writes and put that in; the marker must not reach the model, and `validate.py`
  fails the column if it does. The enum case is a finding as well as a gap
  (`findings.md`, stage 2, pattern 8).

**Interfaces with one implementation**: see the rule in section 2.

Do not draw an edge for something you only assume. If you cannot find the caller,
leave it out and say so in the report.

## 5. Flows

**Inventory first, then choose.** Before writing a single flow, list *every* entry
point in the app - this is the step people skip, and it is why diagrams end up with
three use cases when the app has twenty:

```bash
rg -n '@(Get|Post|Put|Patch|Delete|Request)Mapping' --glob '**/*.kt' --glob '**/*.java'
rg -n '@(EventListener|TransactionalEventListener|KafkaListener|RabbitListener|JmsListener)' --glob '**/*.kt' --glob '**/*.java'
rg -n '@Scheduled' --glob '**/*.kt' --glob '**/*.java'
```

Write that list down with the target method next to each entry - method, path,
what it does. Every one of them is a candidate use case, because behind every
endpoint there is something a person wanted to do.

**Then merge and cut, deliberately:**

- Endpoints whose path through the code is the same shape get **one** flow. `GET
  /customers` and `GET /customers/{id}` both go controller → api → service →
  repository; one of them represents both.
- Everything that crosses a module boundary, publishes an event, calls out to
  another system, or has a guard in it (a lock, a permission check, a state
  machine) gets its **own** flow. That is the knowledge nobody can grep for.
- An endpoint that only reads one repository and returns is a thin flow - but it
  still shows which repository answers it, so it stays unless another flow already
  walks the identical chain.

Forty endpoints means somewhere around forty flows. The list scrolls, and a use case
nobody clicks costs nothing - three flows for an app with twenty endpoints means the
inventory step was skipped.

**A step that repeats in nearly every flow still goes into every flow.** An
`AuthTokenFilter` in front of 32 of 36 endpoints is not boilerplate to be factored
out - the renderer only ever shows one flow at a time, so a flow has to tell the
truth about *that* request on its own. Leave the guard out of the 32 and the picture
says the request goes straight into the controller, which is the thing someone opened
the diagram to check.

The repetition also pays for itself: the four flows *without* the filter are only
visible as an exception because the other 32 carry it. That contrast is a finding
(`findings.md`, stage 4, pattern 25) and it cannot be seen any other way. Keep the
guard as step 1 with a note that says what it checks; the flow `description` does not
have to repeat it.

**Say what you dropped.** The report lists every entry point that did *not* get a
flow, one line each, with the reason ("same path as X", "returns a constant").
That way the reader can tell a deliberate cut from an oversight.

Then trace each flow through the code, exactly like following a request. Every hop
must be an edge that already exists in the model. If a hop is missing, the edge
list is incomplete - fix it there, do not invent a step.

The same edge may appear twice in one flow, and that is where the timing shows: a
client that pulls the attachments in step 2 and acknowledges the message in step 9
walks the same arrow, and the two notes say which is which.

Notes on the steps are the whole point. "checks that the tenant is active" tells
you something, "calls requireActive" does not.

## 6. Sanity check before you hand it over

Run the validator - it is every check the renderer does on load, plus the two it
does not do, and it fails instead of writing a note into a sidebar box:

```bash
python3 $SKILL/assets/validate.py docs/mw-topomap-20260826/model-4.json
```

Errors it stops on: duplicate node, edge or flow ids (a duplicate edge id silently
overwrites its twin, and a flow step then walks the wrong arrow), edges pointing at
nodes that are not there, flow steps that resolve to no edge, an entry pointing at
an unknown node, an unknown module on a node. Warnings it prints: unknown
stereotypes, entities without table or columns, labels too long for their arrow.

What no validator can check for you:

- **every cross-module edge fits the build graph.** Three shapes are allowed to
  break that rule, and all three are legitimate - anything else is a finding:

  | shape | example | why it is fine |
  |---|---|---|
  | interface -> impl | `CustomerFacade -> CustomerFacadeImpl` | runs against the compile direction, Spring wires it at runtime |
  | event edge | `OrderService -> OrderCreatedListener` | no compile coupling, only the event type is shared |
  | interface in the shared module, bean elsewhere | `QueueDao` in `common`, `QueueDaoImpl` in `outbound` | the caller only ever sees `common` |

  The third one is worth a line in the report either way: an architecture test on
  the classpath cannot see it, because on the classpath there is only `common`.

- **the flow steps are in execution order**, and each note says something a reader
  could not have guessed.
- **every entry point is either a flow or a line in the report.**
