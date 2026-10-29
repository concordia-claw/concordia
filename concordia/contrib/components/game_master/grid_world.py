# Copyright 2026 DeepMind Technologies Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A grid world: a toroidal map of terrain whose food regrows, for a GM.

`Grid` is a seeded map of terrain kinds (grass, forest, river, coast,
hills, marsh), each tile carrying food up to its kind's capacity and
growing it back each step, logistically, with a small seed bank so that
bare land greens again. Ridges of hills may part the map into valleys, with
a pass. Entities forage the richest tiles within a day's walk; a mover
looks for the best land within a few steps.

`GridWorld` holds a grid as a game master's context component, so that
the GM's other components (those that resolve moves, make observations or
keep the census) read and change one map under one lock, and so that it
is saved and restored with the GM. It adds nothing to prompts: what an
entity knows of the land, it is told.

  grid = grid_world.Grid(rows=16, cols=24, seed=0, richness=0.5)
  world = grid_world.GridWorld(grid)
  with world.lock:
    taken = world.grid.harvest((3, 4), effort=2.0)
    world.grid.regrow()
"""

from collections.abc import Mapping, Sequence
import threading
from typing import Any, override

from concordia.typing import entity as entity_lib
from concordia.typing import entity_component
import numpy as np

# Terrain kinds, and the food a tile of each carries at most.
TERRAIN = ('grass', 'forest', 'river', 'coast', 'hills', 'marsh')
CAPACITY: Mapping[str, float] = {
    'grass': 6.0,
    'forest': 5.0,
    'river': 9.0,
    'coast': 8.0,
    'hills': 2.5,
    'marsh': 4.0,
}
# The logistic rate food regrows by in a step, and the share of its
# capacity even a bare tile regrows.
REGROWTH = 0.6
SEED_BANK = 0.1

Tile = tuple[int, int]


class Grid:
  """Terrain and food on a toroidal grid (not thread-safe: see `GridWorld`)."""

  def __init__(
      self,
      rows: int,
      cols: int,
      seed: int,
      richness: float = 1.0,
      regrowth: float = REGROWTH,
      seed_bank: float = SEED_BANK,
      capacity: Mapping[str, float] = CAPACITY,
      ridges: Sequence[Mapping[str, Any]] = (),
  ):
    """Makes the grid, its terrain drawn from the seed.

    Args:
      rows: The map's rows.
      cols: The map's columns (it wraps east to west, and north to south).
      seed: Draws the terrain.
      richness: Scales every tile's capacity.
      regrowth: The logistic rate food regrows by in a step.
      seed_bank: The share of its capacity even a bare tile regrows.
      capacity: The food a tile of each terrain kind carries at most.
      ridges: Lines of hills from edge to edge, each at column `col`,
        `width` columns wide (2 by default), with a pass of grass at rows
        `gap` (first and last), if any. The map wraps, so two ridges part
        two valleys altogether.
    """
    self.rows, self.cols = int(rows), int(cols)
    self.richness = float(richness)
    self.regrowth = float(regrowth)
    self.seed_bank = float(seed_bank)
    self._capacity = {kind: float(capacity[kind]) for kind in TERRAIN}
    rng = np.random.default_rng([seed, 1])
    # A smooth random field picks the terrain: rivers in its valleys, hills
    # on its heights, a coast along one edge.
    field = rng.random((self.rows, self.cols))
    for _ in range(3):
      field = (
          field
          + np.roll(field, 1, 0)
          + np.roll(field, -1, 0)
          + np.roll(field, 1, 1)
          + np.roll(field, -1, 1)
      ) / 5.0
    lo, hi = np.quantile(field, [0.12, 0.85])
    wet = rng.random((self.rows, self.cols))
    terrain = np.full((self.rows, self.cols), TERRAIN.index('grass'))
    terrain[field > hi] = TERRAIN.index('hills')
    terrain[field < lo] = TERRAIN.index('river')
    middle = (field >= lo) & (field <= hi)
    terrain[middle & (wet < 0.25)] = TERRAIN.index('forest')
    terrain[middle & (wet > 0.93)] = TERRAIN.index('marsh')
    terrain[:, 0] = TERRAIN.index('coast')
    for ridge in ridges:
      col, width = int(ridge['col']), int(ridge.get('width', 2))
      low, high = (int(r) for r in ridge.get('gap', (0, -1)))
      for row in range(self.rows):
        kind = 'grass' if low <= row <= high else 'hills'
        for c in range(col, col + width):
          terrain[row, c % self.cols] = TERRAIN.index(kind)
    self.terrain = terrain
    self.food = self.capacities()

  def capacities(self) -> np.ndarray:
    """The food each tile carries at most."""
    return np.array(
        [
            [self._capacity[TERRAIN[t]] * self.richness for t in row]
            for row in self.terrain
        ],
        dtype=float,
    )

  def kind(self, tile: Tile) -> str:
    """A tile's terrain kind."""
    return TERRAIN[int(self.terrain[tile])]

  def wrap(self, row: int, col: int) -> Tile:
    """A tile on the map, wrapped around its edges."""
    return (row % self.rows, col % self.cols)

  def distance(self, a: Tile, b: Tile) -> int:
    """Steps between two tiles, across the wrapped edges (Manhattan)."""
    dr = abs(a[0] - b[0])
    dc = abs(a[1] - b[1])
    return min(dr, self.rows - dr) + min(dc, self.cols - dc)

  def around(self, tile: Tile, radius: int = 1) -> list[Tile]:
    """The tiles within `radius` steps each way (the tile itself first)."""
    r, c = tile
    found = [tile]
    for dr in range(-radius, radius + 1):
      for dc in range(-radius, radius + 1):
        if (dr, dc) != (0, 0):
          found.append(self.wrap(r + dr, c + dc))
    return found

  def food_around(self, tile: Tile) -> float:
    """The food within a day's walk: the tile and its neighbours."""
    return float(sum(self.food[t] for t in self.around(tile)))

  def best_near(self, tile: Tile, radius: int = 1) -> Tile:
    """The tile within `radius` steps whose surroundings hold most food.

    Args:
      tile: Where from.
      radius: How far one looks.

    Returns:
      The best tile (ties: the first in the order `around` gives).
    """
    return max(
        self.around(tile, radius), key=lambda t: round(self.food_around(t), 6)
    )

  def harvest(
      self, tile: Tile, effort: float, spare: Sequence[Tile] = ()
  ) -> float:
    """Takes food within a day's walk of a tile, richest tiles first.

    Args:
      tile: Where the forager is.
      effort: The most food it can take.
      spare: Tiles it leaves alone.

    Returns:
      The food taken.
    """
    wanted = max(0.0, float(effort))
    taken = 0.0
    for place in sorted(
        (t for t in self.around(tile) if t not in spare),
        key=lambda t: (-round(float(self.food[t]), 6), t),
    ):
      if taken >= wanted:
        break
      got = float(min(self.food[place], wanted - taken))
      self.food[place] -= got
      taken += got
    return taken

  def regrow(self, season: float = 1.0) -> None:
    """Food grows back, `season` times as much as in a usual step."""
    capacity = self.capacities()
    self.food += season * (
        self.regrowth * self.food * (1.0 - self.food / capacity)
        + self.seed_bank * capacity
    )
    np.minimum(self.food, capacity, out=self.food)

  def get_state(self) -> dict[str, Any]:
    return {
        'rows': self.rows,
        'cols': self.cols,
        'terrain': self.terrain.astype(int).tolist(),
        'food': self.food.tolist(),
    }

  def set_state(self, state: Mapping[str, Any]) -> None:
    """Restores the terrain and food; the settings stay this grid's.

    Args:
      state: `get_state()` of a grid of the same size.

    Raises:
      ValueError: If the saved grid has another size.
    """
    if (int(state['rows']), int(state['cols'])) != (self.rows, self.cols):
      raise ValueError(
          f'A {state["rows"]}x{state["cols"]} grid cannot be restored into a'
          f' {self.rows}x{self.cols} one.'
      )
    self.terrain = np.array(state['terrain'], dtype=int)
    self.food = np.array(state['food'], dtype=float)


class GridWorld(entity_component.ContextComponent):
  """A grid as a game master's component: one map, one lock, saved with it.

  The GM's other components read and change `grid` holding `lock`. It adds
  nothing to the GM's prompts.
  """

  def __init__(self, grid: Grid):
    super().__init__()
    self._grid = grid
    self._lock = threading.RLock()

  @property
  def grid(self) -> Grid:
    """The grid (hold `lock` to read or change it)."""
    return self._grid

  @property
  def lock(self) -> threading.RLock:
    """The lock that guards the grid."""
    return self._lock

  @override
  def pre_act(self, action_spec: entity_lib.ActionSpec) -> str:
    del action_spec
    return ''

  @override
  def get_state(self) -> entity_component.ComponentState:
    with self._lock:
      return self._grid.get_state()

  @override
  def set_state(self, state: entity_component.ComponentState) -> None:
    with self._lock:
      self._grid.set_state(state)
