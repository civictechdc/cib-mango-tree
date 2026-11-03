# Profiling

In order to improve the performance of an application, it is necessary to understand what it is currently doing, and what parts of the application are taking time and computing resources.

Two widely used options for Python are **cProfile** (stdlib) and **samply** (sampling profiler). For visualizing cProfile output, [snakeviz](https://pypi.org/project/snakeviz/) works well. Samply opens the [Firefox Profiler](https://profiler.firefox.com/) UI in your browser (served locally; browsers do not ship the profiler themselves).

For microbenchmarks in tests, this repo already includes [pytest-benchmark](https://pypi.org/project/pytest-benchmark/) in the `dev` dependency group (`uv run pytest` with benchmark tests).

## Profiling with samply

On desktop, CIB Mango Tree uses multiple processes by default (`multiprocessing` spawn, NiceGUI `native=True`, and analyzer process pools). In that setting, `samply` should be your first choice: it samples across processes and threads. (GitHub Codespaces runs with `native=False` and is a thinner multi-process case.)

Install samply from its [upstream instructions](https://github.com/mstange/samply).

Activate the project environment so `cibmt` is on your `PATH` (see [Installation](../get-started/installation.md)), then:

```
samply record cibmt
```

Or point samply at the venv script directly:

```
samply record .venv/bin/cibmt
```

Running this launches the app as usual. Stop the app (or interrupt the session) when you are done collecting samples.

!!! note
    On macOS, samply often shows native/C frames more clearly than pure-Python stacks; Python frame annotations depend on platform and interpreter signing. See the [Python perf-profiling howto](https://docs.python.org/3/howto/perf_profiling.html) and samply’s docs if you need richer Python stacks.

### Exploring samply output in the browser

When recording finishes, samply saves a profile (by default under `~/.local/share/samply/profiles/` on macOS/Linux, or `%LOCALAPPDATA%\samply\profiles\` on Windows) and opens the Firefox Profiler UI in your default browser. That view covers processes, threads, and which stacks dominate runtime.

The output can still be overwhelming; start from the heaviest stacks and drill down.

## Profiling with cProfile

For simpler, single-process profiling, `cProfile` is often preferred. It does not effectively profile multiple processes, and it does not follow calls across FFI boundaries.

`cProfile` ships with Python. Example:

```
python3 -m cProfile -o profile_name.prof ./my_program.py my_arguments
```

cProfile works best on scripts rather than the full GUI. Prefer extracting the functions you care about (for example an analyzer’s `analyze` path) into a small script or test, then profile that. The library layout under `src/cibmangotree/` makes that straightforward.

### Visualizing .prof files with snakeviz

After the run, visualize with:

```
snakeviz profile_name.prof
```

Install snakeviz from [PyPI](https://pypi.org/project/snakeviz/) if needed. Its view is narrower than samply’s but clearer for call hierarchy and hot functions.

!!! info
    Samply is relatively light. cProfile adds more overhead, especially on CPU-heavy code.

## Alternatives

Also consider [py-spy](https://pypi.org/project/py-spy) with [speedscope](https://speedscope.app) for sampling profiles that are easy to share. For true line-by-line timing of a known hot function, use [line_profiler](https://github.com/pyutils/line_profiler) instead of treating a sampler as line-accurate.

Having a sampler and a call-graph profiler available during development makes it much easier to see where time goes and to fix real bottlenecks.
