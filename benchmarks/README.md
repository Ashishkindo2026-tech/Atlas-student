# Atlas Benchmark Suite

Run locally with:

```bash
python -m benchmarks.atlas_benchmark
```

Results are written to `benchmarks/results/latest.json` and are intended for
local comparison across machines and Atlas runtime configurations.

Record at minimum: Python version, OS, CPU, RAM, model, model quantization,
first-response latency, repeated-response latency, peak RAM, and failures.
