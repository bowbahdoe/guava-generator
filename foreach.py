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

cmd = input("cmd: ")

cwd = os.getcwd()

for module in modules:
    print("------------------------------")
    print(f"guava-{module}")
    print("------------------------------")
    os.chdir(cwd + f"/guava-{module}")
    os.system(cmd)
    os.chdir(cwd)