from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).parent
DIST = ROOT / "dist"
ARTIFACT = DIST / "todo-api.zip"
FILES = ("app.py", "index.html", "README.md")


def main():
    DIST.mkdir(exist_ok=True)
    with ZipFile(ARTIFACT, "w", ZIP_DEFLATED) as archive:
        for filename in FILES:
            archive.write(ROOT / filename, filename)
    print("Created %s" % ARTIFACT)


if __name__ == "__main__":
    main()
