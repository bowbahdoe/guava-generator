import os

modules = [
    "base",
    "primitives",
    "escape",
    "math",
    "collect",
    "xml",
    "html",
    "graph",
    "hash",
    "io",
    "net",
    "reflect",
    "concurrent"
]

cwd = os.getcwd()

for module in modules:
    os.chdir(cwd + f"/guava-{module}")
    os.system("mvn clean compile")
    os.chdir(cwd)