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

"""Tests for the grid world."""

from absl.testing import absltest
from concordia.agents import entity_agent_with_logging
from concordia.components.agent import concat_act_component
from concordia.contrib.components.game_master import grid_world
from concordia.language_model import no_language_model
from concordia.typing import entity as entity_lib
import numpy as np


class GridTest(absltest.TestCase):

  def test_the_terrain_is_drawn_from_the_seed(self):
    a = grid_world.Grid(8, 12, seed=3)
    b = grid_world.Grid(8, 12, seed=3)
    c = grid_world.Grid(8, 12, seed=4)

    np.testing.assert_array_equal(a.terrain, b.terrain)
    self.assertFalse(np.array_equal(a.terrain, c.terrain))
    self.assertEqual({a.kind((r, 0)) for r in range(8)}, {'coast'})
    np.testing.assert_array_equal(a.food, a.capacities())  # Full at first.

  def test_a_ridge_parts_the_land_but_for_its_pass(self):
    grid = grid_world.Grid(
        10, 20, seed=0, ridges=[{'col': 9, 'width': 2, 'gap': [4, 5]}]
    )

    for col in (9, 10):
      self.assertEqual(
          [r for r in range(10) if grid.kind((r, col)) == 'hills'],
          [0, 1, 2, 3, 6, 7, 8, 9],
      )
      self.assertEqual(grid.kind((4, col)), 'grass')

  def test_the_map_wraps(self):
    grid = grid_world.Grid(10, 20, seed=0)

    self.assertEqual(grid.wrap(-1, 21), (9, 1))
    self.assertEqual(grid.distance((0, 0), (9, 19)), 2)
    self.assertLen(grid.around((0, 0), 1), 9)
    self.assertIn((9, 19), grid.around((0, 0), 1))

  def test_a_forager_takes_the_richest_tiles_first_and_spares_some(self):
    grid = grid_world.Grid(6, 6, seed=0)
    grid.food[:] = 1.0
    grid.food[2, 2] = 5.0
    grid.food[2, 3] = 4.0

    taken = grid.harvest((2, 2), effort=6.0, spare=[(2, 3)])

    self.assertEqual(taken, 6.0)
    self.assertEqual(grid.food[2, 2], 0.0)
    self.assertEqual(grid.food[2, 3], 4.0)  # Spared.
    self.assertAlmostEqual(float(grid.food.sum()), 43.0 - 6.0)  # 34 + 5 + 4.

  def test_food_grows_back_towards_capacity_and_more_in_a_good_season(self):
    lean = grid_world.Grid(6, 6, seed=0, regrowth=0.5, seed_bank=0.1)
    good = grid_world.Grid(6, 6, seed=0, regrowth=0.5, seed_bank=0.1)
    for grid in (lean, good):
      grid.food[:] = 0.0

    lean.regrow(season=0.5)
    good.regrow(season=1.5)

    capacity = lean.capacities()
    np.testing.assert_allclose(lean.food, 0.05 * capacity)
    np.testing.assert_allclose(good.food, 0.15 * capacity)
    for _ in range(100):
      good.regrow()
    np.testing.assert_allclose(good.food, capacity)  # Never beyond it.

  def test_bare_land_stays_bare_and_every_kind_needs_a_capacity(self):
    grid = grid_world.Grid(
        4, 4, seed=0, capacity={**grid_world.CAPACITY, 'grass': 0.0}
    )
    grid.regrow()

    self.assertFalse(np.isnan(grid.food).any())
    with self.assertRaisesRegex(ValueError, 'No capacity for terrain: marsh'):
      grid_world.Grid(
          4,
          4,
          seed=0,
          capacity={
              k: v for k, v in grid_world.CAPACITY.items() if k != 'marsh'
          },
      )

  def test_a_mover_finds_the_best_land_near(self):
    grid = grid_world.Grid(10, 10, seed=0)
    grid.food[:] = 0.0
    grid.food[5, 5] = 9.0

    self.assertIn(grid.best_near((2, 2), radius=2), grid.around((5, 5)))
    self.assertEqual(grid.best_near((2, 2), radius=0), (2, 2))


class GridWorldTest(absltest.TestCase):

  def test_the_grid_is_saved_and_restored_with_its_game_master(self):
    def game_master(seed):
      return entity_agent_with_logging.EntityAgentWithLogging(
          agent_name='Land',
          act_component=concat_act_component.ConcatActComponent(
              model=no_language_model.NoLanguageModel()
          ),
          context_components={
              grid_world.DEFAULT_GRID_WORLD_COMPONENT_KEY: grid_world.GridWorld(
                  grid_world.Grid(6, 8, seed=seed)
              )
          },
      )

    def world_of(gm):
      return gm.get_component(
          grid_world.DEFAULT_GRID_WORLD_COMPONENT_KEY,
          type_=grid_world.GridWorld,
      )

    gm = game_master(seed=1)
    world = world_of(gm)
    with world.lock:
      world.grid.harvest((3, 3), effort=4.0)
    state = world.get_state()

    again = game_master(seed=2)
    again.set_state(gm.get_state())
    restored = world_of(again)

    np.testing.assert_array_equal(restored.grid.terrain, world.grid.terrain)
    np.testing.assert_array_equal(restored.grid.food, world.grid.food)
    self.assertEqual(
        world.pre_act(entity_lib.free_action_spec(call_to_action='?')), ''
    )
    with self.assertRaisesRegex(ValueError, '6x8 grid cannot'):
      grid_world.GridWorld(grid_world.Grid(5, 5, seed=0)).set_state(state)


if __name__ == '__main__':
  absltest.main()
