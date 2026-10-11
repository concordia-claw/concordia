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

"""Player configuration tests; every provider, game and listener is mocked."""

import contextlib
import io
import pathlib
import tempfile
import unittest
from urllib.parse import urljoin
from html.parser import HTMLParser
from unittest import mock

from concordia.examples.rain_ledger import model_setup
from concordia.examples.rain_ledger import run
from fastapi.testclient import TestClient


class PlayerModelTest(unittest.TestCase):

  def test_missing_protected_credential_fails_before_game_or_listener(self):
    with tempfile.TemporaryDirectory() as directory:
      with (
          mock.patch('sys.argv', ['rain', '--output', directory]),
          mock.patch.object(model_setup.os, 'getenv', return_value=None),
          mock.patch.object(run.game, 'Game') as game,
          mock.patch.object(run.uvicorn, 'run') as server,
          contextlib.redirect_stderr(io.StringIO()) as error,
      ):
        with self.assertRaises(SystemExit) as failure:
          run.main()
        self.assertEqual(failure.exception.code, 2)
        self.assertIn('protected inherited credential', error.getvalue())
        game.assert_not_called()
        server.assert_not_called()
        self.assertFalse(list(pathlib.Path(directory).iterdir()))

  def test_player_uses_together_default_and_existing_transport_on_loopback(
      self,
  ):
    with tempfile.TemporaryDirectory() as directory:
      with (
          mock.patch(
              'sys.argv',
              [
                  'rain',
                  '--output',
                  directory,
                  '--allowed-host',
                  'phone.example.ts.net',
              ],
          ),
          mock.patch.object(model_setup, 'protected_together_model') as model,
          mock.patch.object(run.game, 'Game') as game,
          mock.patch.object(run.web, 'create_app') as web,
          mock.patch.object(run.uvicorn, 'run') as server,
          contextlib.redirect_stdout(io.StringIO()),
      ):
        run.main()
        model.assert_called_once_with(model_setup.DEFAULT_MODEL)
        self.assertIs(game.call_args.args[0], model.return_value)
        self.assertEqual(server.call_args.kwargs['host'], '127.0.0.1')
        self.assertEqual(server.call_args.kwargs['port'], 8795)
        self.assertEqual(
            web.call_args.kwargs['allowed_hosts'],
            ['127.0.0.1', 'localhost', 'phone.example.ts.net'],
        )
        game.return_value.controller.stop.assert_called_once()
        game.return_value.server.stop.assert_called_once()

  def test_player_prefix_assets_and_state_without_game_or_action(self):
    class References(HTMLParser):

      def __init__(self):
        super().__init__()
        self.urls = []

      def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'link'):
          url = attrs.get('src') or attrs.get('href', '')
          if url and not url.startswith('data:'):
            self.urls.append(url)

    for prefix in ('', '/rain-ledger/'):
      with (
          self.subTest(prefix=prefix),
          tempfile.TemporaryDirectory() as directory,
      ):
        ledger = run.rules.Ledger()
        session = run.game.RainSession(ledger)
        with (
            mock.patch(
                'sys.argv',
                [
                    'rain',
                    '--output',
                    directory,
                    '--root-path',
                    prefix,
                    '--allowed-host',
                    'phone.example.ts.net',
                ],
            ),
            mock.patch.object(model_setup, 'protected_together_model'),
            mock.patch.object(run.game, 'Game') as game,
            mock.patch.object(run.uvicorn, 'run') as listener,
            mock.patch.object(session, 'submit') as submit,
            contextlib.redirect_stdout(io.StringIO()),
        ):
          game.return_value.session = session
          run.main()
          app = listener.call_args.args[0]
          root = prefix.rstrip('/')
          self.assertEqual(app.root_path, root)
          # No lifespan context: never run the adventure's runner.
          client = TestClient(app, base_url='https://phone.example.ts.net')
          try:
            if root:
              redirect = client.get(root, follow_redirects=False)
              self.assertEqual(redirect.status_code, 307)
              self.assertEqual(
                  redirect.headers['location'],
                  'https://phone.example.ts.net' + root + '/',
              )
            for preserved in (True, False):
              external = 'https://phone.example.ts.net' + root + '/'

              def upstream(relative):
                path = urljoin(external, relative).removeprefix(
                    'https://phone.example.ts.net'
                )
                return path if preserved or not root else path[len(root) :]

              response = client.get(upstream(''))
              self.assertEqual(response.status_code, 200)
              self.assertIn('The Rain', response.text)
              refs = References()
              refs.feed(response.text)
              self.assertIn('transport.js', refs.urls)
              self.assertIn('static/ledger.js', refs.urls)
              for ref in refs.urls + [
                  'api/journal',
              ]:
                self.assertEqual(
                    client.get(upstream(ref)).status_code, 200, ref
                )
              state = client.get(upstream('api/state'))
              self.assertEqual(state.status_code, 200)
              self.assertEqual(state.json()['casebook']['turn'], 0)
              self.assertFalse(state.json()['casebook']['history'])
          finally:
            client.close()
          submit.assert_not_called()
          game.return_value.play.assert_not_called()
          self.assertEqual(ledger.public()['cash'], 18)

  def test_old_local_model_draft_is_rejected_before_configuration(self):
    with (
        mock.patch('sys.argv', ['rain', '--output', 'unused', '--no-think']),
        mock.patch.object(model_setup, 'protected_together_model') as model,
        contextlib.redirect_stderr(io.StringIO()),
    ):
      with self.assertRaises(SystemExit):
        run.main()
      model.assert_not_called()


if __name__ == '__main__':
  unittest.main()
