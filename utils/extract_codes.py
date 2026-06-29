import os
import sys
from pathlib import Path

IGNORE_DIRS = {".venv", "__pycache__", ".git", ".idea", "venv", "env"}

def should_ignore(file_path: Path) -> bool:
    for part in file_path.parts:
        if part in IGNORE_DIRS or part.startswith(".") and part != ".":
            return True
    return False

def compile_py_to_txt(source_dir: str, output_dir: str = ".", output_filename: str = "compiled_code.txt") -> None:
    source = Path(source_dir).resolve()
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / output_filename

    if not source.is_dir():
        print(f"Error: {source} is not a valid directory.")
        sys.exit(1)

    all_py = list(source.rglob("*.py"))
    py_files = [f for f in all_py if not should_ignore(f)]

    if not py_files:
        print(f"No .py files found outside ignored folders in {source}")
        return

    print(f"Found {len(py_files)} .py files (ignoring .venv and others).")
    print(f"Writing concatenated code to: {output_file}")

    with open(output_file, "w", encoding="utf-8") as out:
        for py_file in sorted(py_files):
            relative_path = py_file.relative_to(source)
            out.write(f"\n\n{'='*80}\n")
            out.write(f"FILE: {relative_path}\n")
            out.write(f"{'='*80}\n\n")

            try:
                content = py_file.read_text(encoding="utf-8")
                out.write(content)
            except Exception as e:
                out.write(f"Error reading file: {e}\n")

    print("Compilation complete.")

def main():
    source = os.getcwd()
    output_dir = "."

    if len(sys.argv) >= 2:
        source = sys.argv[1]
    if len(sys.argv) >= 3:
        output_dir = sys.argv[2]

    compile_py_to_txt(source, output_dir)

if __name__ == "__main__":
    main()