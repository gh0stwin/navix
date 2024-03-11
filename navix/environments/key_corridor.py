from __future__ import annotations

from typing import Tuple, Union
import jax
import jax.numpy as jnp
from jax import Array
import jax.tree_util as jtu
from flax import struct

from ..components import EMPTY_POCKET_ID
from ..rendering.cache import RenderingCache
from ..rendering.registry import PALETTE
from ..environments import Environment
from ..entities import Ball, State, Player, Key, Door, Goal, Wall
from ..environments import Timestep
from ..grid import (
    mask_by_coordinates,
    room,
    random_positions,
    random_directions,
    random_colour,
    vertical_wall,
    horizontal_wall,
    RoomsGrid,
)
from .registry import register_env


class KeyCorridor(Environment):

    def reset(self, key: Array, cache: Union[RenderingCache, None] = None) -> Timestep:
        n_rows_config = {3: 1, 5: 2}
        n_rows = n_rows_config.get(self.height, 3)
        room_size = (self.width - 3) // 3
        k1, k2, k3, k4, k5, k6 = jax.random.split(key, num=6)

        # grid of rooms
        grid = RoomsGrid.create(n_rows, 3, (room_size, room_size))

        # key
        key_room_row = jax.random.randint(k1, (), minval=0, maxval=n_rows)
        key_pos = grid.position_in_room(
            key_room_row, jnp.asarray(0, dtype=jnp.int32), key=k1
        )
        key_colour = random_colour(k4)
        key_id = jnp.asarray(1)
        key_obj = Key.create(key_pos, key_colour, key_id)

        # agent
        pk_1, pk_2, pk_3 = jax.random.split(k2, num=3)
        agent_room_row = jax.random.randint(pk_1, (), minval=0, maxval=n_rows)
        agent_pos = grid.position_in_room(agent_room_row, jnp.asarray(1), key=pk_2)
        player = Player.create(
            agent_pos, random_directions(pk_3), pocket=EMPTY_POCKET_ID
        )

        # ball
        ball_room_row = jax.random.randint(k3, (), minval=0, maxval=n_rows)
        ball_pos = grid.position_in_room(ball_room_row, jnp.asarray(2), key=k4)
        ball = Ball.create(ball_pos, random_colour(k6), probability=jnp.asarray(0.0))

        # Doors
        doors = []
        for row in range(n_rows):
            k5, k6, k7, k8, k9 = jax.random.split(k5, num=5)
            # left corridor, right wall
            door_pos = grid.position_on_border(row, 2, 0, key=k5)
            requires, colour, open = jax.lax.cond(
                jnp.array_equal(row, ball_room_row),
                lambda: (key_id, key_colour, jnp.asarray(2)),
                lambda: (jnp.asarray(-1), random_colour(k5), jnp.asarray(0)),
            )
            doors.append(
                Door.create(
                    position=door_pos, requires=requires, colour=colour, open=open
                )
            )
            # right corridor, left wall
            door_pos = grid.position_on_border(row, 0, 1, key=k7)
            doors.append(
                Door.create(
                    position=door_pos,
                    requires=EMPTY_POCKET_ID,
                    colour=random_colour(k7),
                    open=jnp.asarray(0),
                )
            )
        for row in range(n_rows - 1):
            k9, k10, k11, k12 = jax.random.split(k9, num=4)
            # first col
            door_pos = grid.position_on_border(row, 0, 3, key=k9)
            doors.append(
                Door.create(
                    position=door_pos,
                    requires=EMPTY_POCKET_ID,
                    colour=random_colour(k10),
                    open=jnp.asarray(0),
                )
            )
            doors.append(
                Door.create(
                    position=door_pos,
                    requires=EMPTY_POCKET_ID,
                    colour=random_colour(k12),
                    open=jnp.asarray(0),
                )
            )
        doors = jtu.tree_map(lambda *x: jnp.stack(x), *doors)

        entities = {
            "player": player[None],
            "key": key_obj[None],
            "door": doors,
            "goal": ball[None],
        }

        grid = grid.get_grid()
        grid = grid.at[
            1 + room_size : self.height - 1 : room_size + 1,
            1 + room_size + 1 : 1 + room_size + 1 + room_size,
        ].set(0)
        state = State(
            key=key,
            grid=grid,
            cache=cache or RenderingCache.init(grid),
            entities=entities,
        )
        return Timestep(
            t=jnp.asarray(0, dtype=jnp.int32),
            observation=self.observation(state),
            action=jnp.asarray(-1, dtype=jnp.int32),
            reward=jnp.asarray(0.0, dtype=jnp.float32),
            step_type=jnp.asarray(0, dtype=jnp.int32),
            state=state,
        )


register_env(
    "Navix-KeyCorridorS3R1-v0",
    lambda *args, **kwargs: KeyCorridor(*args, **kwargs, height=3, width=7),
)
register_env(
    "Navix-KeyCorridorS3R2-v0",
    lambda *args, **kwargs: KeyCorridor(*args, **kwargs, height=5, width=7),
)
register_env(
    "Navix-KeyCorridorS3R3-v0",
    lambda *args, **kwargs: KeyCorridor(*args, **kwargs, height=7, width=7),
)
register_env(
    "Navix-KeyCorridorS4R3-v0",
    lambda *args, **kwargs: KeyCorridor(*args, **kwargs, height=10, width=10),
)
register_env(
    "Navix-KeyCorridorS5R3-v0",
    lambda *args, **kwargs: KeyCorridor(*args, **kwargs, height=13, width=13),
)
register_env(
    "Navix-KeyCorridorS6R3-v0",
    lambda *args, **kwargs: KeyCorridor(*args, **kwargs, height=16, width=16),
)
