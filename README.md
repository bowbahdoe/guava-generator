# guava-generator

This is a collection of python scripts which serve the purpose of mechanically repackaging and modularizing
[Guava](https://github.com/google/guava)

- `reset.py` will set each of the submodules to their most recent `main`
- `upgrade.py` will do a find+replace of a version string in the required files for each submodule
- `foreach.py` will run a command for each submodule
- `compile.py` will attempt to run `mvn compile` for each submodule
- `generate.py` will update the code of all of the submodules to the given commit hash of guava
- `commit.py` will push changes to remote repos

## Usage

Consult the repos for the subprojects for the latest releases and dependency information.

* [dev.mccue.guava](https://github.com/bowbahdoe/guava)
* [dev.mccue.guava.base](https://github.com/bowbahdoe/guava-base)
* [dev.mccue.guava.primitives](https://github.com/bowbahdoe/guava-primitives)
* [dev.mccue.guava.escape](https://github.com/bowbahdoe/guava-escape)
* [dev.mccue.guava.math](https://github.com/bowbahdoe/guava-math)
* [dev.mccue.guava.collect](https://github.com/bowbahdoe/guava-collect)
* [dev.mccue.guava.xml](https://github.com/bowbahdoe/guava-xml)
* [dev.mccue.guava.html](https://github.com/bowbahdoe/guava-html)
* [dev.mccue.guava.graph](https://github.com/bowbahdoe/guava-graph)
* [dev.mccue.guava.hash](https://github.com/bowbahdoe/guava-hash)
* [dev.mccue.guava.io](https://github.com/bowbahdoe/guava-io)
* [dev.mccue.guava.net](https://github.com/bowbahdoe/guava-net)
* [dev.mccue.guava.reflect](https://github.com/bowbahdoe/guava-reflect)
* [dev.mccue.guava.concurrent](https://github.com/bowbahdoe/guava-concurrent)

## Changes made from Guava

* Everything is shaded under `dev.mccue.guava`
    * `com.google.common.util.concurrent` is turned into `dev.mccue.guava.concurrent`, dropping the `util`
* All usages of `sun.misc.Unsafe` are removed
    * The unsafe implementation is removed, leaving a safe fallback in `LittleEndianByteArray`, `AbstractFuture`, and `UnsignedBytes`
    * The unsafe implementation in is replaced with a new one based on `VarHandle`s in `Striped64`
* All usages of `sun.misc.JavaLangAccess` are removed
    * Replaced with `Throwable.getStackTrace` in `Throwables`
* All usages of `finalize()` are removed
    * `FileBackedOutputStream` has a constructor which takes a boolean to indicate that resources should be freed on finalization. This was made private and the logic was removed.
* All usages of the Security Manager are removed
    * `Types` catches an `AccessControlException` and that could safely be replaced with catching an `Exception`
    * Explicit uses of the security manager in `LittleEndianByteArray`, `AbstractFuture`, `UnsignedBytes`,  and `Striped64` were removed along with the code to load `sun.misc.Unsafe`.
* All usages of `java.util.logging.Logger` were replaced with `java.lang.System.Logger`
    * With this change, the only JDK module depended on is `java.base`.
* All usages of `javax.annotation.*` classes from `com.google.code.findbugs/jsr305` are replaced with equivalent classes from `dev.mccue/jsr305`
* `FinalizableReferenceQueue` and associated classes were removed
    * They were rarely used, probably do a job better done by a `Cleaner`, and I wasn't able to validate that they would behave correctly in a module
* Annotation modules are used via `requires static` and are not carried over to dependents.
* All annotation usages from `com.google.common.annotations` and `com.google.j2objc.annotations` have been removed
* Split into multiple submodules, each with their own `module-info.java`
* Drops explicit support for GWT, j2objc, j2cl, etc.
* Drops explicit support for android (equivalent to the `-jre` build)
* Does not include
  * `com.google.common.eventbus` (Guava docs explicitly recommends against its use)
  * `com.google.common.cache` ([Caffiene](https://github.com/ben-manes/caffeine) covers that use.)
  * `com.google.common.annotations` (Only `@Beta` and `@VisibleForTesting` would be relevant without GWT+etc. testing, and you can make your own pretty easily.)
* Compiled for Java 9+, not Java 8

## Graph 

![Graph of dependencies](https://github.com/bowbahdoe/guava-generator/assets/5004262/6abfda23-1a05-4a51-8927-ff98edf2156a)

