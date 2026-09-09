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

"""Serve Bellwether; only explicit editor Run executes the one-turn fixture."""

import argparse
import pathlib
import time

from concordia.examples.bellwether import service
from concordia.utils import simulation_server
from concordia.utils import visual_interface


def main(argv=None):
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--editor-port', type=int, default=8784)
  parser.add_argument('--player-port', type=int, default=8785)
  parser.add_argument(
      '--output',
      type=pathlib.Path,
      default=pathlib.Path('runs/bellwether-fixture'),
  )
  args = parser.parse_args(argv)
  game = service.Bellwether(args.output, port=args.editor_port)
  player = simulation_server.SimulationServer(
      port=args.player_port,
      html_content=pathlib.Path(__file__)
      .with_name('player.html')
      .read_text(encoding='utf-8'),
      operation_service=game.operations,
      audience='player',
  )
  game.server.set_html_content(
      visual_interface.visualize_operations_to_html(
          game.config, title='Bellwether · fixture editor'
      )
  )
  try:
    game.server.start()
    player.start()
    print(f'Editor: http://127.0.0.1:{game.server.bound_port}', flush=True)
    print(f'Player: http://127.0.0.1:{player.bound_port}', flush=True)
    print(
        'Fixture only. Explicit run.start executes one human turn; no live'
        ' resident decisions.',
        flush=True,
    )
    while True:
      time.sleep(0.5)
  except KeyboardInterrupt:
    pass
  finally:
    game.close()
    player.stop()


if __name__ == '__main__':
  main()
