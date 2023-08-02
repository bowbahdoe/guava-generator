import os 

modules = [
    "aggregator",
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

old_version = input("current version: ")
next_version = input("next version: ")

cwd = os.getcwd()

for module in modules:
    if module == "aggregator":
        pom_path = "./guava/pom.xml"
        readme_path = "./guava/README.md"
    else:
        pom_path = f"./guava-{module}/pom.xml"
        readme_path = f"./guava-{module}/README.md"

    
    with open(pom_path, "r") as f:
        pom = "".join([line for line in f])

    with open(readme_path, "r") as f:
        readme = "".join([line for line in f])

    pom = pom.replace(old_version, next_version)
    readme = readme.replace(old_version, next_version)

    with open(pom_path, "w") as f:
        f.write(pom)

    with open(readme_path, "w") as f:
        f.write(readme)

workflow_yaml_path = "./guava/.github/workflows/release.yml"

with open(workflow_yaml_path, "r") as f:
    workflow_yaml = "".join([line for line in f])
workflow_yaml = workflow_yaml.replace(old_version, next_version)
with open(workflow_yaml_path, "w") as f:
    f.write(workflow_yaml)

