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

"""Portable public records, not executable replay or component checkpoints."""

import html
import json

from concordia.examples.bellwether import game
from concordia.utils import operation_service as ops

NOTICE = (
    'Public events only. Private journals, component state and service identity'
    ' are excluded. Public speech can still disclose identifying information;'
    ' this is not anonymization. This account is not a checkpoint, executable'
    ' replay, or evidence about real people.'
)


def document(world: game.StormNight, *, fixture: bool, phase: str) -> dict:
  """Project an explicit public allowlist from the standard spectator view."""
  public = world.view('spectator')
  epilogue = public['epilogue']
  return {
      'schema': 'bellwether-public-account/v1',
      'scope': 'public',
      'backend': 'fixture' if fixture else 'live',
      'status': (
          'completed'
          if phase == 'completed'
          else 'interrupted'
          if phase == 'failed'
          else 'in_progress'
      ),
      'watch': public['watch'],
      'notice': NOTICE,
      'events': [
          {
              'number': index,
              'watch': (
                  game.WATCHES[event['watch']] if event['watch'] < 3 else 'Dawn'
              ),
              'kind': event['kind'],
              'text': event['text'],
          }
          for index, event in enumerate(public['journal'], start=1)
      ],
      'accounting': {
          'inventory': {
              owner: {
                  item: public['inventory'][owner][item]
                  for item in ('fuel', 'part')
              }
              for owner in ('Generator', 'Nell', 'Ivo', 'Used')
          },
          'repair_completed': public['repair'],
          'services': [
              {
                  key: record[key]
                  for key in ('watch', 'facility', 'served', 'consequence')
              }
              for record in public['services']
          ],
      },
      'dawn': (
          {
              key: epilogue[key]
              for key in (
                  'services_maintained',
                  'services_total',
                  'fuel_used',
                  'repair_completed',
                  'dispute_settled',
              )
          }
          if epilogue
          else None
      ),
  }


def render_html(account: dict) -> str:
  """Render only a projected document as inert, offline UTF-8 HTML."""
  escape = html.escape
  events = ''.join(
      '<li><h3>'
      + escape(event['watch'])
      + '</h3><p>'
      + escape(event['text'])
      + '</p><small>'
      + escape(event['kind'])
      + '</small></li>'
      for event in account['events']
  )
  if not events:
    events = '<li>No public events recorded yet.</li>'

  def cells(values):
    return ''.join('<td>' + escape(str(value)) + '</td>' for value in values)

  material = account['accounting']
  stocks = ''.join(
      '<tr>' + cells((owner, items['fuel'], items['part'])) + '</tr>'
      for owner, items in material['inventory'].items()
  )
  services = (
      ''.join(
          '<li><strong>'
          + escape(record['watch'])
          + ' · '
          + escape(record['facility'])
          + '</strong><p>'
          + escape(record['consequence'])
          + '</p></li>'
          for record in material['services']
      )
      or '<li>No watch boundary has been resolved yet.</li>'
  )
  dawn = account['dawn']
  conclusion = (
      str(dawn['services_maintained'])
      + ' of '
      + str(dawn['services_total'])
      + ' facility-watches supplied. '
      + str(dawn['fuel_used'])
      + ' fuel consumed in the cumulative Used ledger (including any declared'
      ' pre-play consumption). '
      + (
          'The beacon was repaired.'
          if dawn['repair_completed']
          else 'The beacon was not repaired.'
      )
      + ' These records do not settle the previous-storm dispute.'
      if dawn
      else 'No dawn outcome has been recorded yet.'
  )
  accounting = (
      '<table><caption>Recorded stocks</caption><thead><tr>'
      '<th scope="col">Holder</th><th scope="col">Fuel</th>'
      '<th scope="col">Spare parts</th></tr></thead><tbody>'
      + stocks
      + '</tbody></table><h3>Service consequences</h3><ul>'
      + services
      + '</ul><h3>Dawn</h3><p>'
      + escape(conclusion)
      + '</p>'
  )
  return (
      '<!doctype html><html lang="en"><meta charset="utf-8">'
      '<meta name="viewport" content="width=device-width,initial-scale=1">'
      '<meta http-equiv="Content-Security-Policy" '
      "content=\"default-src 'none'; style-src 'unsafe-inline';"
      " base-uri 'none'; form-action 'none'\">"
      '<title>Bellwether · Public account</title><style>'
      'body{font:1.1rem/1.6 system-ui,sans-serif;max-width:48rem;'
      'margin:auto;padding:1.2rem;color:#162934;background:#f8faf9;'
      'overflow-wrap:anywhere}li{margin-bottom:1.5rem}'
      'p{white-space:pre-wrap;overflow-wrap:anywhere}'
      'table{border-collapse:collapse;width:100%}'
      'td,th{text-align:left;padding:.4rem;border-bottom:1px solid #aabbb8}'
      'caption{text-align:left;font-weight:bold}small{color:#465a64}</style>'
      '<main><h1>Bellwether · Public account</h1><p>'
      + escape(account['backend'].capitalize())
      + ' · '
      + escape(account['status'].replace('_', ' ').capitalize())
      + ' · '
      + escape(account['watch'])
      + '</p><p>'
      + escape(account['notice'])
      + '</p><h2>Public timeline</h2><ol>'
      + events
      + '</ol><h2>Recorded material consequences</h2>'
      + accounting
      + '</main></html>'
  )


def export(
    world: game.StormNight, *, fixture: bool, phase: str, format_name: str
) -> dict:
  """Return artifact content without transport/session envelope identifiers."""
  if format_name not in ('json', 'html'):
    raise ops.OperationError('invalid_format', 'Choose json or html.')
  account = document(world, fixture=fixture, phase=phase)
  return {
      'filename': 'bellwether-public-account.' + format_name,
      'media_type': (
          'application/json; charset=utf-8'
          if format_name == 'json'
          else 'text/html; charset=utf-8'
      ),
      'content': (
          json.dumps(account, ensure_ascii=False, indent=2) + '\n'
          if format_name == 'json'
          else render_html(account)
      ),
  }
