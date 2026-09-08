# Copyright 2024 DeepMind Technologies Limited.
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

"""HTTP server for real-time simulation visualization.

This module provides a server that serves the visualization UI and broadcasts
simulation updates via Server-Sent Events (SSE).
"""

from collections.abc import Callable
import copy
import http.server
import json
import queue
import socketserver
import sys
import threading
from typing import Any

from concordia.environment import step_controller as step_controller_lib
from concordia.typing import prefab as prefab_lib
from concordia.utils import project_config
from concordia.utils import visual_interface


class SimulationServer:
  """HTTP server for real-time simulation control and visualization.

  Features:
    - Serves static HTML visualization
    - Server-Sent Events endpoint for real-time step updates
    - POST endpoints for play/pause/step control
  """

  def __init__(
      self,
      port: int = 8080,
      html_content: str = '',
      host: str = '127.0.0.1',
  ):
    """Initialize the simulation server.

    Args:
      port: Port to serve on.
      html_content: Static HTML content to serve at the root.
      host: Interface to bind to. Defaults to the loopback interface only,
        since this server has no authentication and its endpoints (including
        `/cmd/set_component_state`, which can overwrite arbitrary simulation
        state) are unauthenticated. Pass '0.0.0.0' explicitly to accept
        connections from other machines on the network.
    """
    self._project_lock = threading.RLock()
    self._project_registry: project_config.Registry | None = None
    self._project_document: dict[str, Any] | None = None
    self._project_revision = 0
    self._project_run: dict[str, Any] = {'status': 'not_started'}
    self._project_runner: Callable[[prefab_lib.Config], None] | None = None
    self._project_thread: threading.Thread | None = None
    self._runtime_html = ''
    self._port = port
    self._html_content = html_content
    self._host = host
    self._step_controller = step_controller_lib.StepController(
        start_paused=True
    )
    self._server_sent_events_queues: list[queue.Queue[str]] = []
    self._server_sent_events_lock = threading.Lock()
    self._current_step_data: dict[str, Any] = {}
    self._cached_entity_info: dict[str, Any] | None = None
    self._simulation: Any = None
    self._server: socketserver.TCPServer | None = None
    self._server_thread: threading.Thread | None = None
    print(f'[SERVER INIT] SimulationServer initialized on port {port}')
    sys.stdout.flush()

  @property
  def host(self) -> str:
    """Get the interface the server binds to."""
    return self._host

  @property
  def port(self) -> int:
    """Get the port the server was configured to listen on.

    If the server was started with `port=0`, use `bound_port` instead to get
    the OS-assigned port actually in use.
    """
    return self._port

  @property
  def bound_port(self) -> int:
    """Get the port the running server is actually bound to.

    Raises:
      RuntimeError: If the server has not been started.
    """
    if self._server is None:
      raise RuntimeError('Server has not been started.')
    return self._server.server_address[1]

  @property
  def step_controller(self) -> step_controller_lib.StepController:
    """Get the step controller for use by the simulation."""
    return self._step_controller

  @property
  def html_content(self) -> str:
    """Get the HTML content to serve."""
    return self._html_content

  @property
  def current_step_data(self) -> dict[str, Any]:
    """Get the current step data."""
    return self._current_step_data

  @property
  def server_sent_events_lock(self) -> threading.Lock:
    """Get the lock for thread-safe Server-Sent Events queue access."""
    return self._server_sent_events_lock

  @property
  def server_sent_events_queues(self) -> list[queue.Queue[str]]:
    """Get the list of Server-Sent Events client queues."""
    return self._server_sent_events_queues

  @property
  def cached_entity_info(self) -> dict[str, Any] | None:
    """Get cached entity info for new SSE clients."""
    return self._cached_entity_info

  def set_html_content(self, html_content: str) -> None:
    """Update the HTML content to serve."""
    self._html_content = html_content

  def set_simulation(self, simulation: Any) -> None:
    """Set the simulation instance for dynamic state editing.

    This must be called after the Simulation object is created so that
    the server can forward edit requests to it.

    Args:
      simulation: The Simulation instance.
    """
    self._simulation = simulation

  @property
  def simulation(self) -> Any:
    """Get the simulation instance."""
    return self._simulation

  def broadcast_step(self, step_data: step_controller_lib.StepData) -> None:
    """Broadcast step data to all connected Server-Sent Events clients.

    Args:
      step_data: The step data to broadcast.
    """
    self._current_step_data = {
        'step': step_data.step,
        'acting_entity': step_data.acting_entity,
        'action': step_data.action,
        'entity_actions': step_data.entity_actions,
        'entity_logs': step_data.entity_logs,
        'game_master': step_data.game_master,
    }
    message = f'data: {json.dumps(self._current_step_data)}\n\n'
    with self._server_sent_events_lock:
      dead_queues = []
      for q in self._server_sent_events_queues:
        try:
          q.put_nowait(message)
        except queue.Full:
          dead_queues.append(q)
      for q in dead_queues:
        self._server_sent_events_queues.remove(q)

  def broadcast_completion(self) -> None:
    """Broadcast simulation completion to all connected SSE clients."""
    completion_data = {
        'completion': True,
        'message': 'Simulation completed!',
    }
    message = f'data: {json.dumps(completion_data)}\n\n'
    with self._server_sent_events_lock:
      for q in self._server_sent_events_queues:
        try:
          q.put_nowait(message)
        except queue.Full:
          pass

  def broadcast_entity_info(self, checkpoint_data: dict[str, Any]) -> None:
    """Broadcast entity component info to all connected SSE clients.

    This sends the initial checkpoint data (containing component metadata)
    so the inspector panel can display component information in serve mode.

    Args:
      checkpoint_data: The checkpoint data from sim.make_checkpoint_data().
    """
    entity_info = {
        'entity_info': True,
        'entities': checkpoint_data.get('entities', {}),
        'game_masters': checkpoint_data.get('game_masters', {}),
    }
    self._cached_entity_info = entity_info
    message = f'data: {json.dumps(entity_info)}\n\n'
    with self._server_sent_events_lock:
      for q in self._server_sent_events_queues:
        try:
          q.put_nowait(message)
        except queue.Full:
          pass

  def configure_project(
      self,
      registry: project_config.Registry,
      document: dict[str, Any],
      run: Callable[[prefab_lib.Config], None],
  ) -> None:
    """Enable initial-project authoring with a trusted, caller-owned runner.

    The runner receives a fresh Config and is invoked only by explicit Run.
    It should bind the new standard Simulation to this server, provide its
    runtime visualization, and call Simulation.play with the existing controller
    and broadcast callbacks. Saving a draft never changes the bound simulation.
    """
    normalized = registry.normalize(document)
    with self._project_lock:
      if self._project_registry is not None:
        raise RuntimeError('Project authoring is already configured.')
      if self._simulation is not None:
        raise RuntimeError(
            'Configure the initial project before binding runtime state.'
        )
      self._project_registry = registry
      self._project_document = normalized
      self._project_runner = run
      self.set_html_content(
          visual_interface.visualize_config_to_html(
              registry.to_config(normalized),
              project_mode=True,
              title='Initial project',
          )
      )

  def get_project(self) -> dict[str, Any]:
    """Get an owned initial draft and its separate run status."""
    with self._project_lock:
      if self._project_document is None:
        raise ValueError('Initial-project authoring is not configured.')
      return copy.deepcopy({
          'document': self._project_document,
          'revision': self._project_revision,
          'run': self._project_run,
      })

  def replace_project(self, text: str, revision: int) -> dict[str, Any]:
    """Atomically replace a valid draft; reject stale or active-run edits."""
    with self._project_lock:
      if self._project_registry is None:
        raise ValueError('Initial-project authoring is not configured.')
      self._check_project_revision(revision)
      normalized = self._project_registry.loads(text)
      html = visual_interface.visualize_config_to_html(
          self._project_registry.to_config(normalized),
          title='Initial project',
          project_mode=True,
      )
      self._project_document = normalized
      self.set_html_content(html)
      self._project_revision += 1
      return self.get_project()

  def _check_project_revision(self, revision: int) -> None:
    if self._project_run['status'] == 'active':
      raise ValueError(
          'A run is active (including paused). Finish it before replacing or'
          ' running a project.'
      )
    if (
        not isinstance(revision, int)
        or isinstance(revision, bool)
        or revision != self._project_revision
    ):
      raise ValueError(
          'The draft changed in another tab. Reopen the current draft before'
          ' saving.'
      )

  def run_project(self, revision: int) -> dict[str, Any]:
    """Start the saved revision, rejecting concurrent runs."""
    with self._project_lock:
      if self._project_registry is None or self._project_runner is None:
        raise ValueError('Initial-project authoring is not configured.')
      self._check_project_revision(revision)
      config = self._project_registry.to_config(self._project_document)
      self._project_run = {'status': 'active', 'revision': revision}
      self._step_controller = step_controller_lib.StepController(
          start_paused=False
      )
      self._current_step_data = {}
      self._cached_entity_info = None
      self._runtime_html = ''
      self._project_thread = threading.Thread(
          target=self._run_project, args=(config,), daemon=True
      )
      self._project_thread.start()
      return self.get_project()

  def _run_project(self, config: prefab_lib.Config) -> None:
    outcome = {'status': 'completed'}
    try:
      assert self._project_runner is not None
      self._project_runner(config)
    except Exception as error:  # pylint: disable=broad-exception-caught
      # Retain a failed draft for correction/export, not a lost thread.
      outcome = {'status': 'failed', 'message': str(error)}
    finally:
      with self._project_lock:
        # Publish completion only after this run's controller is finalized.
        self._step_controller.pause()
        self._project_run.update(outcome)

  @property
  def runtime_html_content(self) -> str:
    """Get the bound runtime visualization, separate from the initial draft."""
    return self._runtime_html

  def set_runtime_html_content(self, html_content: str) -> None:
    """Set the existing runtime inspector, separate from the initial draft."""
    self._runtime_html = html_content

  def _create_handler(self):
    """Create a request handler class with access to server state."""
    server = self

    class Handler(http.server.BaseHTTPRequestHandler):
      """HTTP request handler for simulation server."""

      def log_message(self, format: str, *args: Any) -> None:  # pylint: disable=redefined-builtin
        """Suppress HTTP request logging."""
        del format, args  # Unused

      def do_GET(self) -> None:  # pylint: disable=invalid-name
        """Handle GET requests for HTML, Server-Sent Events, status, and commands."""
        print(f'[SERVER] GET request received: {self.path}')

        sys.stdout.flush()
        if self.path == '/project':
          try:
            self._send_json(server.get_project())
          except ValueError as error:
            self._send_json({'error': str(error)}, 400)
        elif self.path == '/runtime':
          if server.runtime_html_content:
            self._serve_html(server.runtime_html_content)
          else:
            self.send_error(404, 'Run the initial project first.')
        elif self.path == '/':
          self._serve_html()
        elif self.path == '/events':
          self._serve_server_sent_events()
        elif self.path == '/status':
          self._serve_status()
        # GET-based command endpoints for testing
        elif self.path == '/cmd/step':
          print('[SERVER] GET /cmd/step - calling step()')
          sys.stdout.flush()
          server.step_controller.step()
          self._send_json({'status': 'stepping', 'method': 'GET'})
        elif self.path == '/cmd/play':
          print('[SERVER] GET /cmd/play - calling play()')
          sys.stdout.flush()
          server.step_controller.play()
          self._send_json({'status': 'playing', 'method': 'GET'})
        elif self.path == '/cmd/pause':
          print('[SERVER] GET /cmd/pause - calling pause()')
          sys.stdout.flush()
          server.step_controller.pause()
          self._send_json({'status': 'paused', 'method': 'GET'})
        else:
          self.send_error(404)

      def do_POST(self) -> None:  # pylint: disable=invalid-name
        """Handle POST requests for simulation control commands."""
        if self.path in ('/project', '/project/run'):
          self._handle_project()
        elif self.path == '/play':
          print('[SERVER] Calling step_controller.play()...')
          server.step_controller.play()
          print('[SERVER] play() completed, sending response...')
          self._send_json({'status': 'playing'})
          print('[SERVER] Response sent for /play')
        elif self.path == '/pause':
          print('[SERVER] Calling step_controller.pause()...')
          server.step_controller.pause()
          print('[SERVER] pause() completed, sending response...')
          self._send_json({'status': 'paused'})
          print('[SERVER] Response sent for /pause')
        elif self.path == '/step':
          print('[SERVER] Calling step_controller.step()...')
          server.step_controller.step()
          print('[SERVER] step() completed, sending response...')
          self._send_json({'status': 'stepping'})
          print('[SERVER] Response sent for /step')
        elif self.path == '/stop':
          print('[SERVER] Calling step_controller.stop()...')
          server.step_controller.stop()
          print('[SERVER] stop() completed, sending response...')
          self._send_json({'status': 'stopped'})
          print('[SERVER] Response sent for /stop')
        elif self.path == '/cmd/set_component_state':
          self._handle_set_component_state()
        else:
          print(f'[SERVER] Unknown path: {self.path}')
          self.send_error(404)

      def _serve_html(self, html_content: str | None = None) -> None:
        """Serve the visualization HTML."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(
            (
                server.html_content if html_content is None else html_content
            ).encode('utf-8')
        )

      def _serve_status(self) -> None:
        """Serve current simulation status."""
        status = {
            'is_running': server.step_controller.is_running,
            'is_paused': server.step_controller.is_paused,
            'current_step': server.current_step_data.get('step', 0),
        }
        self._send_json(status)

      def _serve_server_sent_events(self) -> None:
        """Serve Server-Sent Events stream."""
        self.send_response(200)
        self.send_header('Content-type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        server_sent_events_queue: queue.Queue[str] = queue.Queue(maxsize=100)
        with server.server_sent_events_lock:
          server.server_sent_events_queues.append(server_sent_events_queue)

        if server.current_step_data:
          initial = f'data: {json.dumps(server.current_step_data)}\n\n'
          self.wfile.write(initial.encode('utf-8'))
          self.wfile.flush()

        # Send cached entity info if available
        if server.cached_entity_info:
          entity_info_msg = (
              f'data: {json.dumps(server.cached_entity_info)}\n\n'
          )
          self.wfile.write(entity_info_msg.encode('utf-8'))
          self.wfile.flush()

        try:
          while True:
            try:
              message = server_sent_events_queue.get(timeout=30)
              self.wfile.write(message.encode('utf-8'))
              self.wfile.flush()
            except queue.Empty:
              self.wfile.write(b': keepalive\n\n')
              self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
          pass
        finally:
          with server.server_sent_events_lock:
            if server_sent_events_queue in server.server_sent_events_queues:
              server.server_sent_events_queues.remove(server_sent_events_queue)

      def _handle_project(self) -> None:
        """Initial-project requests do not use the runtime-state endpoint."""
        try:
          length = int(self.headers.get('Content-Length', 0))
          if not 0 < length <= 1024 * 1024:
            self.close_connection = True
            raise ValueError(
                'Project request must be between 1 byte and 1 MiB.'
            )
          request = json.loads(self.rfile.read(length).decode('utf-8'))
          if self.path == '/project/run':
            result = server.run_project(request['revision'])
          else:
            result = server.replace_project(
                request['text'], request['revision']
            )
          self._send_json(result)
        except (
            KeyError, ValueError, TypeError, UnicodeError, RecursionError
        ) as error:
          self._send_json({'error': str(error)}, 400)

      def _handle_set_component_state(self) -> None:
        """Handle POST /cmd/set_component_state for dynamic editing."""
        if not server.step_controller.is_paused:
          self._send_json({
              'status': 'error',
              'message': 'Simulation must be paused to edit state.',
          })
          return

        if server.simulation is None:
          self._send_json({
              'status': 'error',
              'message': 'No simulation instance available.',
          })
          return

        try:
          content_length = int(self.headers.get('Content-Length', 0))
          body = self.rfile.read(content_length)
          data = json.loads(body.decode('utf-8'))

          entity_name = data['entity_name']
          component_name = data['component_name']
          key = data['key']
          value = data['value']

          server.simulation.set_component_dynamic_state(
              entity_name=entity_name,
              component_name=component_name,
              key=key,
              value=value,
          )

          # Broadcast updated entity info so inspector refreshes
          checkpoint_data = server.simulation.make_checkpoint_data()
          server.broadcast_entity_info(checkpoint_data)

          print(
              f'[SERVER] Updated dynamic state: {entity_name}.'
              f'{component_name}.{key}'
          )
          self._send_json({
              'status': 'ok',
              'message': f'Updated {entity_name}.{component_name}.{key}',
          })
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as e:
          print(f'[SERVER] Error setting component state: {e}')
          self._send_json({'status': 'error', 'message': str(e)})

      def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    return Handler

  def start(self) -> None:
    """Start the HTTP server in a background thread."""
    handler = self._create_handler()
    self._server = socketserver.ThreadingTCPServer(
        (self._host, self._port), handler
    )
    self._server.allow_reuse_address = True
    self._server_thread = threading.Thread(target=self._server.serve_forever)
    self._server_thread.daemon = True
    self._server_thread.start()
    print(f'Simulation server running at http://localhost:{self._port}')

  def stop(self) -> None:
    """Stop the HTTP server."""
    if self._server:
      self._server.shutdown()
      self._server = None
    if self._server_thread:
      self._server_thread.join(timeout=5)
      self._server_thread = None
