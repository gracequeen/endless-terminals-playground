# Goal

Original pipeline already has skyrl integration. But task and solution pair formats are not Harbor format. We need to integrate both parts together, as described in: https://novasky-ai.notion.site/skyrl-harbor and https://www.harborframework.com/docs/agents/terminus-2. 

Test PPO algorithm with passing test or not as the reward. 


# Things to Be Cautious

- Don't look at folders like "harbor_tasks...." or "Solutions". These are the task and solution datasets, which are A LOT, wasting your time. 
- Original model loading from vllm for smaller models from qwen and llama. Here our model endpoints for generation are from SAP aicore library. Then during skyrl training, vllm components also need to be adjusted accordingly. 
