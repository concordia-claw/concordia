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

"""Scenario model configuration using the standard Together adapter."""

import os
from typing import cast

DEFAULT_MODEL = 'deepseek-ai/DeepSeek-V4.1-Flash'


def protected_together_model(model_name, credential=None):
  """Use the standard adapter with an explicitly authorized SDK endpoint."""
  from concordia.contrib.language_models.together import together_ai_model
  import together

  if credential is None:
    credential = os.getenv('TOGETHER_API_KEY') or os.getenv(
        'TOGETHER_AI_API_KEY'
    )
  if not credential:
    raise ValueError('Together requires a protected inherited credential')
  client = together.Together(
      api_key=credential,
      base_url='https://api.together.xyz/v1',
      max_retries=0,
      timeout=30,
  )
  return together_ai_model.Base(
      model_name=model_name,
      api_key=credential,
      client=cast(together_ai_model.TogetherClient, client),
  )
