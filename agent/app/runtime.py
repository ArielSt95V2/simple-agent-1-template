from dataclasses import dataclass
from typing import Any

from psycopg_pool import ConnectionPool

from agent.app.checkpoints import open_checkpoint_pool
from agent.app.config import Settings, load_agent_profile
from agent.graph.react import build_compiled_graph


@dataclass
class AgentRuntime:
    settings: Settings
    profile: dict
    graph: Any
    checkpoint_pool: ConnectionPool

    def close(self) -> None:
        self.checkpoint_pool.close()


def create_runtime(settings: Settings) -> AgentRuntime:
    profile = load_agent_profile(settings)
    pool = open_checkpoint_pool(settings)
    try:
        graph = build_compiled_graph(settings, profile, pool)
    except Exception:
        pool.close()
        raise
    return AgentRuntime(settings=settings, profile=profile, graph=graph, checkpoint_pool=pool)
