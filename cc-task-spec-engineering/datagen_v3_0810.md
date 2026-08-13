- extra small testing: 64 tasks; small batch for testing: 192 tasks; normal batch: 5120
- output-dir: harbor_tasks_v3_<small-test/test/normal>
- model: opus 4.8
- max-tokens: 8192
- difficulty: mixed
- difficulty distribution: easy=0.2, medium=0.4, hard=0.4
- batch-size: 16 
- max-concurrency: 16
- pipeline-depth: 6
The rest parameters use default value.
