import ast
import os
import sys
from pathlib import Path


def recompile_code(source: str) -> str:
    tree = ast.parse(source)
    return ast.unparse(tree)


def process_file(path: Path) -> bool:
    try:
        original = path.read_text(encoding="utf-8")
        new = recompile_code(original)
        if new != original:
            path.write_text(new, encoding="utf-8")
            return True
        return False
    except SyntaxError as e:
        print(f"error: cannot parse {path}: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"error: {path}: {e}", file=sys.stderr)
        return False


def is_hidden(path: Path) -> bool:
    return any((part.startswith(".") for part in path.parts))


def collect_files(paths):
    for p in paths:
        path = Path(p)
        if p == "-":
            yield "-"
        elif path.is_file() and path.suffix == ".py":
            if not is_hidden(path):
                yield path
        elif path.is_dir():
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for name in files:
                    if name.endswith(".py") and (not name.startswith(".")):
                        yield (Path(root) / name)


def main():
    if len(sys.argv) < 2:
        print("usage: python recompile.py [files or directories or -]", file=sys.stderr)
        sys.exit(1)
    targets = sys.argv[1:]
    files = list(collect_files(targets))
    if not files:
        print("No Python files found.", file=sys.stderr)
        return
    changed = 0
    total = 0
    for f in files:
        total += 1
        if f == "-":
            try:
                source = sys.stdin.read()
                result = recompile_code(source)
                sys.stdout.write(result)
            except Exception as e:
                print(f"error: stdin: {e}", file=sys.stderr)
            continue
        if process_file(f):
            changed += 1
            print(f"recompiled {f}")
        else:
            print(f"unchanged {f}")
    print(f"\n{changed} file(s) reformatted, {total - changed} unchanged.")


if __name__ == "__main__":
    main()
