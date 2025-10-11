Object-Oriented Design Practice Workspace (Java, Gradle)

Quick start for a local, reusable OOD exercise workspace. Multi-project Gradle build with a shared `:common` module, a local question bank, and a generator to spin up new exercises on demand. No cloud dependencies.

Requirements
- Java 21 (JDK)
- Gradle 8+ available as `gradle` on PATH
- Python 3.8+

Create Your First Exercise
- From registry: `bin/new-ex.sh new strategy-pattern-basics --from-registry`
- Ad hoc: `bin/new-ex.sh new ddd-aggregates-intro --title "DDD Aggregates Intro" --prompt "Model a small order system that enforces invariants via aggregate roots" --tags "ddd,aggregates" --difficulty medium`
- List questions: `bin/new-ex.py list` or filter: `bin/new-ex.py list --filter-by-tag patterns`

Run Tests
- Entire workspace: `gradle test`
- Specific subproject: `gradle :common:test` or `gradle :exercises:<slug>:test`

Layout
- `settings.gradle.kts` discovers `:common` and any subprojects under `exercises/*` that contain a `build.gradle.kts`.
- `common/` contains small utilities usable by exercises.
- `templates/exercise-java/` is the generator template for new exercises.
- `registry/questions.yaml` is the local question bank.
- `exercises/` holds generated subprojects. Remains empty until you create your first exercise.

Generator Usage (bin/new-ex.py)
- Create from registry: `bin/new-ex.py new <slug> --from-registry`
- Create ad hoc: `bin/new-ex.py new <slug> --title <str> --prompt <str> --tags <csv> --difficulty <str>`
- Refuses overwrite on collision and suggests `<slug>-v2`, `-v3`, etc.
- Wrapper `bin/new-ex.sh` calls the Python script and touches `settings.gradle.kts` so Gradle re-discovers subprojects on next run.

Question Bank
- Edit `registry/questions.yaml` to add entries. Keys: `slug, title, difficulty, tags, prompt, checklist`.
- Comments allowed with `#`. Multi-line prompts are supported via `|` scalars.

Developer Notes
- All subprojects use Java 21 and JUnit 5.
- Keep scripts idempotent; prior exercises are never deleted.
- Errors are explicit and exit with non-zero codes.

Extensibility
- Add more templates under `templates/`, e.g. `templates/exercise-java-spring`, and pass `--template` to the generator when you’re ready.
