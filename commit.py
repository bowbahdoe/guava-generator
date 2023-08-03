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

print("(Make sure you just ran generate with this commit hash)")
commit_hash = input("Guava Commit Hash: ")

cwd = os.getcwd()

paths = [cwd + "/guava"]
for module in modules:
    paths.append(cwd + f"/guava-{module}")

for path in paths:
    os.chdir(path)

    os.system(f"git checkout -b guava-{commit_hash}")
    os.system("git add src")
    os.system(f"git commit --allow-empty -m \"Sync guava commit {commit_hash}\"")
    os.system(f"git push --set-upstream origin guava-{commit_hash}")