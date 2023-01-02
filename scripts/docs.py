import pydoc
import pathlib

PACKAGE_PATH = pathlib.Path(__file__).parent.parent / "kerykeion" / "kerykeion"
OUTPUT_PATH = pathlib.Path(__file__).parent.parent / "docs"

print(PACKAGE_PATH)

def main():
    # Write documetation for the relative module in path kerykeion, output to "docs" folder
    pydoc.writedocs(dir="OUTPUT_PATH", pkgpath=PACKAGE_PATH)


if __name__ == "__main__":
    main()
