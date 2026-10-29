---
name: java-best-practices
description: Write, refactor, or review Java code using the user's records-first, modern Java, and Project Loom concurrency preferences. Apply to Java data models, language and API choices, and concurrent code, including Java used in Spring applications.
---

# Java best practices

## Match the project Java version

Inspect the build's Java toolchain, compiler release, runtime, and preview flags
before selecting language features or APIs. Prefer modern Java features over
older equivalent boilerplate when they fit the task and are supported by the
project. This includes record patterns, pattern matching, switch expressions,
sealed types, and newer standard-library APIs where useful; it does not require
using every feature in every change.

Consult official Java release notes and version-specific language/API
documentation when choosing newer features. Verify their status in the target
release: features can be final, preview, incubating, changed, or withdrawn.
Do not silently raise the Java baseline. Use preview/incubator features when the
project already enables the required support or the user explicitly chooses
their adoption; otherwise use supported final APIs and explain any limitation.

## Prefer records over POJOs

Always consider a Java record first for a data-carrying type, including request
and response DTOs, value objects, projections, and client payloads. Prefer it to
a hand-written or generated POJO when it can satisfy the type's requirements.
Use compact constructors for invariants when appropriate.

Records have final components, but referenced objects can remain mutable. Use
defensive copies where the contract requires immutable contents. Preserve the
required serialization and validation behavior when converting an existing type.

Use an ordinary class only for a concrete need a record cannot satisfy, such as
required mutable state, class inheritance, or an incompatible framework contract.
Check the actual persistence or binding technology rather than assuming records
work for every entity. Explain the reason for an exception. Service and other
behavioral components do not become records simply to follow this preference.

See the official [record classes guide](https://docs.oracle.com/en/java/javase/25/language/records.html);
select the edition matching the target Java release.

## Prefer Project Loom APIs for concurrency

Use Loom's virtual threads for concurrent blocking I/O when supported by the
project. Prefer task-per-virtual-thread execution over introducing a pool of
platform threads for that workload. Depending on lifecycle needs, use
`Thread.ofVirtual()` or `Executors.newVirtualThreadPerTaskExecutor()`; ensure
tasks are joined or awaited and executors are closed or managed by the framework.

Do not pool virtual threads. Bound access to scarce resources, such as database
connections or remote API capacity, separately. Virtual threads improve the
scalability of blocking work, not CPU execution speed; choose bounded parallelism
appropriate to CPU-bound work. Keep cancellation, interruption, failures, and
timeouts explicit; do not introduce detached background tasks accidentally.

Use structured concurrency for related subtasks and scoped values for suitable
immutable contextual data when their status and APIs in the target release allow
it. Verify preview requirements rather than copying signatures across releases.
Do not assume thread-bound transactions or framework context propagate into new
threads. Respect an existing reactive execution model instead of wrapping it in
blocking virtual-thread calls without a task-specific reason.

Consult the official [virtual threads guide](https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html)
and the target release's concurrency documentation. Framework-managed execution
should use the framework's version-compatible virtual-thread support where
appropriate rather than adding a competing executor.

## Validate the change

Compile and run relevant existing checks with the configured Java release and
flags. For changes to data representation or concurrency, verify affected
serialization contracts or task completion, failure, and cancellation behavior
as relevant to the change. Keep unrelated migrations out of scope.
