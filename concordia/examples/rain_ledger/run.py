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

"""Run the original Rain Ledger using local Ollama and existing human transport."""

import argparse
import pathlib

from concordia.contrib.language_models.ollama import ollama_model
from concordia.examples.astral_canticle import web
from concordia.examples.rain_ledger import game
from fastapi.responses import FileResponse
import uvicorn


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--port', type=int, default=8795)
  parser.add_argument('--editor-port', type=int, default=8796)
  parser.add_argument('--model', default='llama3.2:3b')
  parser.add_argument('--output', type=pathlib.Path, required=True)
  parser.add_argument(
      '--resume',
      action='store_true',
      help='Restore scenario ledger; pending requests receive fresh IDs.',
  )
  parser.add_argument(
      '--checkpoint',
      type=pathlib.Path,
      help='Restore a standard checkpoint into a NEW output directory.',
  )
  parser.add_argument('--allowed-host', action='append', default=[])
  args = parser.parse_args()
  if (args.output / 'ledger.json').exists() and not args.resume:
    parser.error(
        'Existing save: choose --resume explicitly or a fresh output directory.'
    )
  model = ollama_model.OllamaLanguageModel(
      args.model,
      request_timeout=60,
      max_output_tokens=180,
      system_message=(
          'Follow the requested JSON format. You are playing one character, not'
          ' narrating the whole world.'
      ),
  )
  instance = game.Game(
      model,
      args.output,
      port=args.editor_port,
      resume=args.resume,
      checkpoint=args.checkpoint,
  )
  app = web.create_app(
      instance.session,
      runner=instance.play,
      static_path=pathlib.Path(__file__).with_name('static'),
      journal_title='THE RAIN LEDGER',
      journal_filename='rain-ledger.txt',
      allowed_hosts=['127.0.0.1', 'localhost', *args.allowed_host],
  )

  @app.get('/transport.js')
  def transport_script():
    return FileResponse(
        pathlib.Path(web.__file__).with_name('static') / 'app.js',
        media_type='application/javascript',
    )

  @app.post('/api/pause-after-action')
  def pause_after():
    return instance.arm_pause()

  @app.post('/api/resume')
  def resume():
    instance.controller.play()
    return {'resumed': True}

  instance.server.start()
  print(
      f'Rain Ledger player http://127.0.0.1:{args.port}/; private developer'
      f' http://127.0.0.1:{args.editor_port}/',
      flush=True,
  )
  try:
    uvicorn.run(app, host='127.0.0.1', port=args.port)
  finally:
    instance.controller.stop()
    instance.server.stop()


if __name__ == '__main__':
  main()
