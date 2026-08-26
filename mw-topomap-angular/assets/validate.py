#!/usr/bin/env python3
"""Everything the renderer would silently repair, found before anyone opens the page.

    python3 validate.py docs/mw-topomap/model-4.json

Exit code 1 when there are errors, 0 otherwise - so it can guard a build.

**errors** lose data on the way to the picture: a duplicate id that overwrites its
twin, an edge pointing at a node that is not there, a flow step that resolves to no
edge. The page still opens, it just shows something else than the model says.

**warnings** render, only worse than intended: an unknown stereotype turning into a
grey component, an entity without columns, a label too long for its arrow. A stage 1
model has no members and no columns by design, so those checks only start at stage 2.
The findings floor per stage is checked the same way - see findings.md.

Same rules as `topomap check`, without needing node - if topomap is installed, that
command does the same job.
"""
import json
import sys

# keep in sync with src/presets.json in the topomap repo
STEREOTYPES = {
    'spring': ['controller', 'job', 'api', 'facade', 'service', 'usecase', 'component',
               'mapper', 'client', 'event', 'config', 'repository', 'entity'],
    'angular': ['route', 'guard', 'resolver', 'page', 'organism', 'template', 'molecule',
                'atom', 'directive', 'pipe', 'state', 'store', 'api', 'client', 'model',
                'interceptor', 'component', 'config'],
}
THEME_KEYS = {'primary', 'secondary', 'success', 'warning', 'danger', 'info', 'gray',
              'background', 'text', 'accentText', 'fontBase', 'fontMono'}
# meta.stereotypes replaces a definition, it does not merge into it - a half-filled
# entry silently takes the defaults (label = the key, rank 2, cube, grey) for
# everything it leaves out, so all four fields are required here
STEREOTYPE_KEYS = {'label', 'rank', 'icon', 'color'}
ICONS = {'globe', 'door', 'gear', 'cube', 'shuffle', 'cloud', 'bolt', 'clock', 'sliders',
         'db', 'table', 'signpost', 'shield', 'window', 'layout', 'puzzle', 'dot', 'wand'}
MAX_RANK = 5           # beyond the preset columns the header reads "Rank 6"
# what a column type may be; anything else is the Kotlin type that never got mapped
SQL_TYPES = {'uuid', 'text', 'varchar', 'char', 'citext', 'date', 'time', 'timestamp',
             'timestamptz', 'boolean', 'bool', 'smallint', 'integer', 'int', 'int2',
             'int4', 'int8', 'bigint', 'serial', 'bigserial', 'numeric', 'decimal',
             'real', 'double precision', 'float', 'money', 'bytea', 'json', 'jsonb',
             'xml', 'inet', 'cidr', 'macaddr', 'interval', 'tsvector', 'hstore', 'point',
             'blob', 'clob', 'enum', 'array'}
LABEL_LIMIT = 70
# findings.md: three at stage 2, five at stage 3, eight at stage 4 - cumulative, and
# only asked for once the model is big enough that the floor is realistic. Eight
# findings about fifteen classes would be padding, which is what findings.md forbids.
FINDINGS_FLOOR = {2: 3, 3: 5, 4: 8}
FINDINGS_FLOOR_FROM = 25
SEVERITIES = {'high', 'medium', 'low'}


def validate(model):
    errors, warnings = [], []
    if not isinstance(model, dict):
        return ['the model is not a json object'], []

    nodes = model.get('nodes') or []
    modules = model.get('modules') or []
    edges = model.get('edges') or []
    flows = model.get('flows') or []
    meta = model.get('meta') or {}
    if not nodes:
        errors.append('nodes is missing or empty')

    preset = meta.get('preset', 'spring')
    if preset not in STEREOTYPES:
        errors.append(f'unknown meta.preset "{preset}" - use spring or angular')
    custom = meta.get('stereotypes') or {}
    known = set(STEREOTYPES.get(preset, STEREOTYPES['spring'])) | set(custom)
    for name, spec in custom.items():
        if not isinstance(spec, dict):
            errors.append(f'meta.stereotypes["{name}"] is not an object')
            continue
        missing = STEREOTYPE_KEYS - set(spec)
        if missing:
            warnings.append(f'meta.stereotypes["{name}"] has no {", ".join(sorted(missing))} - '
                            f'the renderer replaces the definition instead of merging, so what is '
                            f'left out falls back to the default (label = the key, rank 2, cube, grey)')
        if spec.get('icon') and spec['icon'] not in ICONS:
            warnings.append(f'meta.stereotypes["{name}"]: unknown icon "{spec["icon"]}" - '
                            f'it falls back to cube without a word. Known: {", ".join(sorted(ICONS))}')
        rank = spec.get('rank')
        if isinstance(rank, int) and not 0 <= rank <= MAX_RANK:
            warnings.append(f'meta.stereotypes["{name}"]: rank {rank} sits outside the preset '
                            f'columns, so its header reads "Rank {rank}" instead of a name')
        if name in STEREOTYPES.get(preset, []):
            warnings.append(f'meta.stereotypes["{name}"] overrides a stereotype the {preset} preset '
                            f'already has - it replaces the whole definition, colour and column included')
    for key in meta.get('theme') or {}:
        if key not in THEME_KEYS:
            warnings.append(f'unknown meta.theme key "{key}" - ignored by the renderer')

    module_ids = set()
    for i, m in enumerate(modules):
        mid = m.get('id')
        if not mid:
            errors.append(f'modules[{i}] has no id')
        elif mid in module_ids:
            errors.append(f'duplicate module id "{mid}"')
        module_ids.add(mid)

    stage = meta.get('detail') or (4 if flows else 3 if edges else 1)
    wants_members = stage >= 2 or any(n.get('members') for n in nodes)

    ids = set()
    for i, n in enumerate(nodes):
        nid = n.get('id')
        at = nid or f'nodes[{i}]'
        if not nid:
            errors.append(f'nodes[{i}] has no id')
        elif nid in ids:
            errors.append(f'duplicate node id "{nid}"')
        ids.add(nid)

        stereo = n.get('stereotype')
        if stereo and stereo not in known:
            warnings.append(f'unknown stereotype "{stereo}" on {at} - the renderer shows it as component')
        if modules:
            if not n.get('module'):
                errors.append(f'node {at} has no module - it would land in the unassigned lane')
            elif n['module'] not in module_ids:
                errors.append(f'node {at} references unknown module "{n["module"]}"')

        if stereo == 'entity' and wants_members:
            if not n.get('table'):
                warnings.append(f'entity {at} has no table name')
            columns = n.get('columns') or []
            if not columns:
                warnings.append(f'entity {at} has no columns - the extraction failed, open the file')
            elif not any(c.get('pk') for c in columns):
                warnings.append(f'entity {at} has no primary key - the @MappedSuperclass base is probably missing')
            for c in columns:
                ctype = (c.get('type') or '').strip()
                # "? IracingTeam" is the extractor saying it could not map the type;
                # "iracingteam" is the older shape of the same gap, and both read as a
                # db type to everyone who opens the picture
                base = ctype.split('(')[0].strip().rstrip('[]')
                if ctype.startswith('?') or (base and ' ' not in base and base not in SQL_TYPES
                                             and not ctype.startswith(('collection', 'embedded'))):
                    warnings.append(f'entity {at}: column "{c.get("name")}" has type "{ctype}", '
                                    f'which is not a db type - an @Converter, an @Embeddable or an '
                                    f'enum without @Enumerated, and it has to be filled in by hand')
        if stereo == 'controller' and wants_members and n.get('members') \
                and not any(m.get('http') for m in n['members']):
            warnings.append(f'controller {at} has members but none carries http')

    declared, targets, pairs, long_labels = set(), set(), set(), 0
    for i, e in enumerate(edges):
        at = e.get('id', i)
        for end in ('from', 'to'):
            if e.get(end) not in ids:
                errors.append(f'edge {at}: unknown node "{e.get(end)}"')
        if e.get('id'):
            if e['id'] in declared:
                errors.append(f'duplicate edge id "{e["id"]}" - a flow step would resolve to the wrong edge')
            declared.add(e['id'])
        targets.add(e.get('id') or f'e{i}')
        pairs.add(f'{e.get("from")}>{e.get("to")}')
        if len(e.get('label') or '') > LABEL_LIMIT:
            long_labels += 1

    flow_ids = set()
    for i, f in enumerate(flows):
        at = f.get('id') or f'flows[{i}]'
        if f.get('id'):
            if f['id'] in flow_ids:
                errors.append(f'duplicate flow id "{f["id"]}"')
            flow_ids.add(f['id'])
        if f.get('entry'):
            node_id, _, member = f['entry'].partition('#')
            if node_id not in ids:
                errors.append(f'flow {at}: entry points at unknown node "{node_id}"')
            elif member:
                node = next(n for n in nodes if n.get('id') == node_id)
                if node.get('members') and not any(m.get('name') == member for m in node['members']):
                    warnings.append(f'flow {at}: entry "{f["entry"]}" names a member {node_id} does not have')
        steps = f.get('steps') or []
        if not steps:
            warnings.append(f'flow {at} has no steps - it lights up nothing')
        for j, s in enumerate(steps, start=1):
            hit = s['edge'] in targets if s.get('edge') else f'{s.get("from")}>{s.get("to")}' in pairs
            if not hit:
                where = s.get('edge') or f'{s.get("from")} -> {s.get("to")}'
                errors.append(f'flow {at} step {j} has no matching edge: {where}')
            if len(s.get('note') or '') > LABEL_LIMIT:
                long_labels += 1


    findings = model.get('findings') or []
    floor = FINDINGS_FLOOR.get(stage)
    if floor and len(nodes) >= FINDINGS_FLOOR_FROM and len(findings) < floor:
        warnings.append(f'{len(findings)} finding(s) at stage {stage} - the floor is {floor}, '
                        f'and the report has to say why if it stays below')
    finding_ids = set()
    for i, f in enumerate(findings):
        at = f.get('id') or f'findings[{i}]'
        if f.get('id'):
            if f['id'] in finding_ids:
                errors.append(f'duplicate finding id "{f["id"]}"')
            finding_ids.add(f['id'])
        if not f.get('title'):
            errors.append(f'finding {at} has no title')
        for ref in f.get('nodes') or []:
            if ref not in ids:
                errors.append(f'finding {at}: unknown node "{ref}"')
        for ref in f.get('modules') or []:
            if ref not in module_ids:
                errors.append(f'finding {at}: unknown module "{ref}"')
        # a finding that anchors to nothing cannot be shown next to anything
        if not (f.get('nodes') or f.get('modules')):
            errors.append(f'finding {at} names neither a node nor a module')
        if f.get('severity') and f['severity'] not in SEVERITIES:
            warnings.append(f'finding {at}: unknown severity "{f["severity"]}" - use high, medium or low')
        if not f.get('evidence'):
            warnings.append(f'finding {at} has no evidence - a finding without a count or a file is advice')

    if long_labels:
        warnings.append(f'{long_labels} label(s) or note(s) over {LABEL_LIMIT} characters - they get cut off on the arrow')
    return errors, warnings


def main(paths):
    failed = False
    for path in paths:
        try:
            with open(path, encoding='utf-8') as fh:
                model = json.load(fh)
        except (OSError, ValueError) as exc:
            print(f'x {path}: {exc}')
            failed = True
            continue
        errors, warnings = validate(model)
        for w in warnings:
            print(f'! {w}')
        for e in errors:
            print(f'x {e}')
        counts = (f'{len(model.get("modules") or [])} modules · {len(model.get("nodes") or [])} classes · '
                  f'{len(model.get("edges") or [])} links · {len(model.get("flows") or [])} use cases · '
                  f'{len(model.get("findings") or [])} findings')
        print(f'{"x" if errors else "ok"} {path}  {counts}'
              f'  ({len(errors)} error(s), {len(warnings)} warning(s))')
        failed = failed or bool(errors)
    return 1 if failed else 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
