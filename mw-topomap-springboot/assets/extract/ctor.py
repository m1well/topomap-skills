#!/usr/bin/env python3
"""Class declaration plus the dependency list, for a whole directory of files at once.

    python3 ctor.py $(rg -l '@Service' --glob '**/*.kt')

Kotlin dependencies sit in the primary constructor, which runs over as many lines as
it needs - a service with nineteen of them is not unusual, and that is exactly the
class whose edges you must not miss. So the parentheses are counted rather than a
fixed number of lines being read.

Java has three shapes and all of them show up: constructor injection, Lombok's
@RequiredArgsConstructor over `private final` fields, and field injection with
@Autowired. All three are printed.

Output is the input for writing edges - it is not the model. Read the class before
you draw anything from it.
"""
import re
import sys
import pathlib

KT_CLASS = re.compile(
    r'^\s*(?:@\w+(?:\([^)]*\))?\s+)*'
    r'(?:internal |private |public |open |abstract |sealed |data |value |enum |annotation )*'
    r'(?:class|interface|object) (\w+)')

JAVA_CLASS = re.compile(
    r'^\s*(?:public |final |abstract |sealed )*(?:class|interface|record|enum) (\w+)')
JAVA_FIELD = re.compile(r'^\s*(?:private|protected)\s+(final\s+)?([\w<>\[\], ?.]+?)\s+(\w+)\s*;')
JAVA_CTOR = re.compile(r'^\s*(?:public |protected )?(\w+)\s*\(')
JAVA_AUTOWIRED = re.compile(r'^\s*@Autowired')


def joined(lines, i):
    """The declaration on line i plus every line it runs into, parentheses balanced."""
    buf, depth, j = lines[i], lines[i].count('(') - lines[i].count(')'), i
    while depth > 0 and j + 1 < len(lines):
        j += 1
        buf += ' ' + lines[j].strip()
        depth += lines[j].count('(') - lines[j].count(')')
    return re.sub(r'\s+', ' ', buf).strip()


def kotlin(lines):
    return [f'  L{i + 1}: ' + joined(lines, i)
            for i, line in enumerate(lines) if KT_CLASS.match(line)]


def java(lines):
    out, class_names, pending = [], set(), False
    for i, line in enumerate(lines):
        cls = JAVA_CLASS.match(line)
        if cls:
            class_names.add(cls.group(1))
            out.append(f'  L{i + 1}: ' + joined(lines, i).split('{')[0].strip())
            continue
        field = JAVA_FIELD.match(line)
        # `private final` is the Lombok dependency list; a non-final field only counts
        # when the line above injected it
        if field and (field.group(1) or pending):
            out.append(f'  L{i + 1}:   field {field.group(3)}: {field.group(2)}' +
                       ('   <- @Autowired' if pending else ''))
            pending = False
            continue
        ctor = JAVA_CTOR.match(line)
        if ctor and ctor.group(1) in class_names:
            out.append(f'  L{i + 1}:   ctor ' + joined(lines, i).split('{')[0].strip())
        pending = bool(JAVA_AUTOWIRED.match(line))
    return out


def main(paths):
    for p in paths:
        path = pathlib.Path(p)
        lines = path.read_text(encoding='utf-8').splitlines()
        found = java(lines) if path.suffix == '.java' else kotlin(lines)
        print(f'### {p}')
        print('\n'.join(found) if found else '  (none)')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
