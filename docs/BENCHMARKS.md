# Benchmarks

Compression quality lives in [token-engine](https://github.com/Bossmann007/token-engine).

```bash
cd token-engine
token-engine benchmark --check-baseline
pytest
```

Targets: quality 100%, total ratio improving over time.

Environment-level benchmarks (memory, continue) are manual — see WORKFLOWS.md Test A/B/C.
