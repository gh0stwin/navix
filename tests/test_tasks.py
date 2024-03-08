import jax
import jax.numpy as jnp

import navix as nx
from navix.entities import Entities, Player, Goal, Key, Door
from navix.components import EMPTY_POCKET_ID
from navix.rendering.registry import PALETTE


def test_navigation():
    """Unittest for https://github.com/epignatelli/navix/pull/47"""
    height = 10
    width = 10
    grid = jnp.zeros((height - 2, width - 2), dtype=jnp.int32)
    grid = jnp.pad(grid, 1, mode="constant", constant_values=-1)

    players = Player(
        position=jnp.asarray((1, 1)), direction=jnp.asarray(0), pocket=EMPTY_POCKET_ID
    )
    goals = Goal(
        position=jnp.asarray([(1, 1), (1, 1)]), probability=jnp.asarray([0.0, 0.0])
    )
    keys = Key(position=jnp.asarray((2, 2)), id=jnp.asarray(0), colour=PALETTE.YELLOW)
    doors = Door(
        position=jnp.asarray([(1, 5), (1, 6)]),
        requires=jnp.asarray((0, 0)),
        open=jnp.asarray((False, True)),
        colour=PALETTE.YELLOW,
    )

    entities = {
        Entities.PLAYER: players[None],
        Entities.GOAL: goals,
        Entities.KEY: keys[None],
        Entities.DOOR: doors,
    }

    state = nx.entities.State(
        key=jax.random.PRNGKey(0),
        grid=grid,
        cache=nx.rendering.cache.RenderingCache.init(grid),
        entities=entities,
    )
    action = jnp.asarray(0)
    reward = nx.tasks.navigation(state, action, state)
    assert jnp.array_equal(reward, jnp.asarray(0.0))


def test_tasks_composition():
    reward_fn = nx.tasks.compose(
        nx.tasks.navigation,
        nx.tasks.action_cost,
        nx.tasks.time_cost,
        nx.tasks.wall_hit_cost,
    )

    env = nx.environments.Room(height=3, width=3, max_steps=8, reward_fn=reward_fn)
    key = jax.random.PRNGKey(0)

    def _test():
        timestep = env.reset(key)
        for _ in range(10):
            timestep = env.step(timestep, jax.random.randint(key, (), 0, 7))
        return timestep

    print(jax.jit(_test)())


if __name__ == "__main__":
    # test_tasks_composition()
    test_navigation()
