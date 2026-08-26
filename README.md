# topomap-skills

Two [Claude Code](https://claude.com/claude-code) skills that read a codebase and
write a **topomap model** - the json that [topomap.m1well.com](https://topomap.m1well.com)
renders as an interactive architecture diagram.

| skill | reads |
|---|---|
| `mw-topomap-springboot` | Spring Boot - Kotlin or Java, Gradle or Maven, one module or twenty |
| `mw-topomap-angular` | Angular workspaces - Nx monorepo, classic multi-project or a single app |

The skill produces json and nothing else. No html, no build step, no tooling left
behind in the analysed repo.

## What the diagram answers

Build modules (or Nx projects) become lanes, classes are grouped by stereotype into
columns that line up across every lane, and the arrows between them carry a label
saying what they fetch or do. Behind one button sit the use cases: pick one and the
path a request takes lights up through the modules, step by numbered step.

That last part is the point of the whole thing. Module structure can be read off a
`settings.gradle`; the order in which six classes touch a request cannot.

## Written in four stages

A model for a real application is 60 to 100 KB of written text, and the writing is
where the time goes. So it is written in four passes, and **after each one the file
is finished, named and handed over** before anything else happens:

| stage | what goes in | share of the writing |
|-------|--------------|----------------------|
| 1 | modules, classes, stereotypes | ~10% |
| 2 | what each class offers: members, signatures, entity columns | ~40% |
| 3 | the connections between them, with labels | ~10% |
| 4 | the use cases | ~40% |

Every stage is its own file, `model-1.json` through `model-4.json`, in a folder
dated with the day the run started - `docs/mw-topomap-20260826/`. A run six months
later writes next to it instead of over it, so the old picture stays openable and
the two can be held next to each other.

Every stage opens on its own - stage 1 is the picture you show someone in their
first week, stage 4 is the one you walk a use case through. The skill stops after each stage and
asks whether to continue, narrow the scope, or leave it there. Cutting a module at
stage 1 costs nothing; cutting it at stage 4 wasted an hour of writing.

## Findings come with it

From stage 2 on the model also carries `findings` - what the scan noticed on the way
and would otherwise throw away: the service with 19 constructor parameters, the two
modules that depend on each other, the outbound http call sitting inside a
transaction. Each one names the class and the count that made it a finding, and each
one anchors to nodes the diagram already shows, so a renderer can highlight what a
finding is about.

The rule that keeps the list worth reading: an observation is a finding, advice is
not. "Consider splitting large services" would be true without ever opening the repo.
The patterns, the categories and how many belong in each stage are in
`references/findings.md`.

## Install

Claude Code follows symlinked skill directories, so the repo can live wherever your
other checkouts live:

```bash
git clone https://github.com/m1well/topomap-skills.git
ln -s "$PWD/topomap-skills/mw-topomap-springboot" ~/.claude/skills/mw-topomap-springboot
ln -s "$PWD/topomap-skills/mw-topomap-angular"    ~/.claude/skills/mw-topomap-angular
```

Copying the two directories into `~/.claude/skills/` works just as well, and
`<project>/.claude/skills/` makes a skill available in one repo only.

Then, in the repo you want to look at:

```
/mw-topomap-springboot
/mw-topomap-angular            # or a scope: /mw-topomap-angular apps/shop
```

## What is in a skill

```
mw-topomap-springboot/
  SKILL.md                     the workflow, the stages, the rules that keep it readable
  references/extraction.md     how to find things: grep recipes, name patterns, traps
  references/model-format.md   every field the model may contain
  references/findings.md       what to write down while reading, and how many
  assets/extract/ctor.py       class declaration plus the dependency list
  assets/extract/funs.py       public methods with their full signature
  assets/extract/entity.py     tables, columns, PK/FK, supertypes - as json
  assets/validate.py           every check the renderer does, before the page exists
  examples/model.example.json  a complete small model
```

The extractors exist because reading is not grep work. A Kotlin primary constructor
runs over as many lines as it has parameters, and the class with nineteen of them is
exactly the one whose edges must not come out half missing. Same for entity columns,
which sit in the constructor *or* in the class body and inherit their audit columns
from a `@MappedSuperclass` that is in a different file entirely.

**They also say when they lose something.** A parser that silently prints two of six
methods is worse than no parser at all: the model looks finished, and nothing
downstream can tell that four are missing. So each file is measured twice - the
signatures against the declarations in the class body, the columns against the
properties - and a mismatch goes to stderr with the line numbers. Fewer methods than
`fun` in the file means the extraction failed, not that the class is small.

`validate.py` runs the renderer's own checks offline and splits them: **errors** lose
data on the way to the picture - a duplicate edge id that silently overwrites its
twin, a flow step that resolves to no edge - while **warnings** still render, only
worse than intended.

## Requirements

`python3` for the extractors and the validator, `rg` ([ripgrep](https://github.com/BurntSushi/ripgrep))
for the search recipes. Both are already there on most developer machines.

## Looking at the result

Drop the `model.json` onto [topomap.m1well.com](https://topomap.m1well.com). The page
renders it in the browser - nothing is uploaded, nothing is stored. 

## Copyright and License

Copyright :copyright: 2026 Michael Wellner ([@m1well](https://m1well.com))<br>
Code released under the [MIT License](/LICENSE).<br>
