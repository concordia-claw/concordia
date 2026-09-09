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

"""Serve Bellwether through the standard shared player/editor/CLI service."""

import argparse
import json
import pathlib
import time

from concordia.contrib.language_models.ollama import ollama_model
from concordia.examples.bellwether import game_service
from concordia.examples.bellwether import service
from concordia.language_model import call_limit_wrapper
from concordia.language_model import profiled_language_model
from concordia.utils import profiler
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
  parser.add_argument(
      '--mode',
      choices=('slice', 'fixture', 'live'),
      default='slice',
      help=(
          'slice: original one-turn demo; fixture: scripted full night; live:'
          ' local model residents'
      ),
  )
  parser.add_argument(
      '--resident-prefab', choices=('minimal', 'basic'), default='minimal'
  )
  parser.add_argument('--model', default='llama3.2:3b')
  parser.add_argument(
      '--dispute-file',
      type=pathlib.Path,
      help='Optional JSON with text and recipients for High Tide.',
  )
  args = parser.parse_args(argv)
  dispute = (
      json.loads(args.dispute_file.read_text(encoding='utf-8'))
      if args.dispute_file
      else None
  )
  profile = profiler.ProfilerContext()
  profile.enable()
  model = None
  if args.mode == 'live':
    model = call_limit_wrapper.CallLimitLanguageModel(
        profiled_language_model.ProfiledLanguageModel(
            ollama_model.OllamaLanguageModel(
                args.model,
                request_timeout=90,
                max_output_tokens=256,
                system_message=(
                    'Respond as the instructed resident, with one JSON decision'
                    ' object. No markdown.'
                ),
            ),
            model_name=args.model,
            profiler_instance=profile,
        ),
        max_calls=256,
    )
  game = (
      service.Bellwether(args.output, port=args.editor_port)
      if args.mode == 'slice'
      else game_service.Game(
          args.output,
          port=args.editor_port,
          model=model,
          actor_logic=args.resident_prefab,
          dispute=dispute,
          profiler=profile,
      )
  )
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
          game.config, title='Bellwether · ' + args.mode + ' editor'
      )
  )
  try:
    game.server.start()
    player.start()
    print(f'Editor: http://127.0.0.1:{game.server.bound_port}', flush=True)
    print(f'Player: http://127.0.0.1:{player.bound_port}', flush=True)
    print(
        'Mode: '
        + args.mode
        + '. Explicit Begin / run.start starts this session. No automatic'
        ' replay.',
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
