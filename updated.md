# Code Judge Update Notes

This document covers:

- [Initialization and Registration](#initialization-and-registration)
- [YAML Configuration Format](#yaml-configuration-format)
- [Resource Control Fields](#resource-control-fields)
- [Using Lean](#using-lean)
- [Interpreting Lean Results](#interpreting-lean-results)
- [External Dependencies and Precompilation](#external-dependencies-and-precompilation)

---

<a id="initialization-and-registration"></a>
## Initialization and Registration

When `run_workers.py` is executed for the first time, it will initialize **tool dependencies**.

- Use the `-c` flag to specify the configuration file (default: `config.yaml`):

```bash
python run_workers.py -c config.yaml
```

> A default configuration file `config.yaml` is provided. You can customize it as needed.

---

<a id="yaml-configuration-format"></a>
## YAML Configuration Format

The configuration file describes dependency initialization logic for each tool (e.g., **python**, **cpp**, **lean**).

**Basic structure (excerpted from `config.yaml`):**

```yaml
# worker.default.yaml
# If you need other external repositories, place them under app/libs/external_repository
tools:
  python:
    setup:        # Initialization steps for Python
  cpp:
    setup:        # Initialization steps for C++
  lean:
    setup:        # Initialization steps for Lean
      - type: shell
        name: "git clone external repository repl"
        run: |
          cd app/libs/external_repository/
          git clone https://github.com/leanprover-community/repl.git
      - type: shell
        name: "write dependency to lakefile.toml for repl"
        run: |
          cd app/libs/external_repository/repl
          echo '' >> lakefile.toml
          echo '[[require]]' >> lakefile.toml
          echo 'name = "mathlib"' >> lakefile.toml
          echo 'scope = "leanprover-community"' >> lakefile.toml
      - type: shell
        name: "build repl"
        run: |
          cd app/libs/external_repository/repl
          lake update
          lake build repl
```

**Field description:**

- `tools`: Defines tool categories (commonly `python` / `cpp` / `lean`).
- `setup`: Ordered list of initialization steps; may include multiple `shell` commands.
- Each `setup` step contains:
  - `type`: `shell` in the examples above;
  - `name`: Step display name (useful for logs);
  - `run`: Actual command(s) to execute (multi-line supported).

---

<a id="resource-control-fields"></a>
## Resource Control Fields

New resource control fields are added to a `submission`:

| Field          | Type | Default  | Description                                  |
|----------------|------|----------|----------------------------------------------|
| `timeout`      | int  | `10s`    | Max execution time in seconds                |
| `cpu_core`     | int  | `1`      | Number of CPU cores available to the program |
| `memory_limit` | int  | `256 MB` | Max memory limit in MB                       |

**Example:**

```json
{
  "type": "python",
  "solution": "print('hello')",
  "timeout": 5,
  "cpu_core": 2,
  "memory_limit": 512
}
```

---

<a id="using-lean"></a>
## Using Lean

- Set `type` to `lean` in the `submission`;
- Put your Lean code into the `solution` field;
- **Must** set `expected_output` to an empty string;
- **Remove all `import` statements** in your submission; the system auto-injects required imports (currently **Mathlib** only);
- Execution mode supports `run` only.

**Example:**

```json
{
  "type": "lean",
  "solution": "theorem add_comm (a b : Nat) : a + b = b + a := by simp",
  "expected_output": ""
}
```

---

<a id="interpreting-lean-results"></a>
## Interpreting Lean Results

`pass` = no `errors` and no `sorry` during REPL execution.

**Success:**

```json
{
  "success": true
}
```

**Failure (example):**

```json
{
  "success": false,
  "stderr": "error: proof failed ..."
}
```

---

<a id="external-dependencies-and-precompilation"></a>
## External Dependencies and Precompilation

- Lean execution depends on the **REPL** repository, which is initialized during the **registration** phase.
- To reduce compilation overhead of external libraries, the system uses **pre-compilation**: all external libraries are pre-compiled during registration.

**To add a new external library:**

1. Add the dependency to `PRE_TEMPLATE` in `lean_executor.py`;
2. Modify `config.yaml` to inject the corresponding entries into `lakefile.toml`;
3. Re-run the worker.
