"""Example of using RLlib's debug callbacks.
Here we use callbacks to track the average CartPole pole angle magnitude as a
custom metric.
"""

from typing import Dict
import argparse
import numpy as np

import ray
from ray import tune
from ray.rllib.env import BaseEnv
from ray.rllib.policy import Policy
from ray.rllib.policy.sample_batch import SampleBatch
from ray.rllib.evaluation import MultiAgentEpisode, RolloutWorker
from ray.rllib.agents.callbacks import DefaultCallbacks


class PacketDeliveredCountCallback(DefaultCallbacks):
    def on_episode_start(self, worker: RolloutWorker, base_env: BaseEnv,
                         policies: Dict[str, Policy],
                         episode: MultiAgentEpisode, **kwargs):
        pass
    def on_episode_step(self, worker: RolloutWorker, base_env: BaseEnv,
                        episode: MultiAgentEpisode, **kwargs):
        pass

    def on_episode_end(self, worker: RolloutWorker, base_env: BaseEnv,
                       policies: Dict[str, Policy], episode: MultiAgentEpisode,
                       **kwargs):
        episode.custom_metrics["packet_delivered"] = (base_env.get_unwrapped()[0].get_packet_delivered_count())

    
    def on_sample_end(self, worker: RolloutWorker, samples: SampleBatch,
                      **kwargs):
        #print("returned sample batch of size {}".format(samples.count))
        pass

    def on_train_result(self, trainer, result: dict, **kwargs):
        #print("trainer.train() result: {} -> {} episodes".format(
        #    trainer, result["episodes_this_iter"]))
        # you can mutate the result dict to add new fields to return
        #result["callback_ok"] = True
        pass

    def on_postprocess_trajectory(
            self, worker: RolloutWorker, episode: MultiAgentEpisode,
            agent_id: str, policy_id: str, policies: Dict[str, Policy],
            postprocessed_batch: SampleBatch,
            original_batches: Dict[str, SampleBatch], **kwargs):
        #print("postprocessed {} steps".format(postprocessed_batch.count))
        #if "num_batches" not in episode.custom_metrics:
        #    episode.custom_metrics["num_batches"] = 0
        #episode.custom_metrics["num_batches"] += 1
        pass
    

