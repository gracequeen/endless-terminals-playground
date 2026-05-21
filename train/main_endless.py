import ray
import hydra
from omegaconf import DictConfig
from skyrl.train.utils import initialize_ray
from skyrl.train.entrypoints.main_base import BasePPOExp, config_dir, validate_cfg
from skyrl_gym.envs import register

@ray.remote(num_cpus=1)
def skyrl_entrypoint(cfg: DictConfig):
   register(
      id="endless",
      entry_point="train.sky_endless:SkyRLContainerEnv", 
   )

   exp = BasePPOExp(cfg)
   exp.run()

@hydra.main(config_path=config_dir, config_name="ppo_base_config", version_base=None)
def main(cfg: DictConfig) -> None:
   validate_cfg(cfg)

   initialize_ray(cfg)
   ray.get(skyrl_entrypoint.remote(cfg))

if __name__ == "__main__":
   main()