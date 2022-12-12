import os
from typing import Optional

import boto3

from pydantic import BaseSettings

from availability.ports import EventStoreRepo
from availability.adapters import DynamoEventStoreRepo


class AppContext(BaseSettings):
  env: str = "local"
  port: int = 8000
  availability_channel: str = "availability"
  appointments_channel: str = "appointments"
  aws_region: str = "us-east-1"
  availability_event_store_table: str = "availability_event_store"
  availability_read_model_table: str = "availability_read_model"
  cache: dict = {}

  @property
  def event_store_repo(self) -> EventStoreRepo:
    if "event_store_repo" in self.cache:
      return self.cache["event_store_repo"]

    ddb = boto3.resource('dynamodb', region_name=self.aws_region)
    self.cache["event_store_repo"] = DynamoEventStoreRepo(
      ddb.Table(self.availability_event_store_table)
    )
    return self.cache["event_store_repo"]


def configure(**kwargs):
  """
  Initializes a configurable AppContext which provides abstractions
  to key software architectural layer boundaries like repositories,
  messaging, http, and cli.
  """
  ssm_prefix = 'aws_ssm_'
  ssm_prefix_n = len(ssm_prefix)
  normalized_fields = { k.lower(): k for k in AppContext.__fields__.keys() }

  awsenv = { k.lower()[ssm_prefix_n:]: v
            for k, v in os.environ.items()
            if k.lower().startswith(ssm_prefix) }

  # add any aws overrides from **kwargs
  for key in kwargs.keys():
    if key.lower().startswith(ssm_prefix):
      ssm_key = key.lower()[ssm_prefix_n:]
      awsenv[ssm_key] = kwargs.pop(key)

  aws_ssm_fields = normalized_fields.keys() & awsenv.keys()

  if not aws_ssm_fields:
      return AppContext(**kwargs)

  ssm = boto3.client('ssm')
  overrides = {}
  for field in aws_ssm_fields:
      response = ssm.get_parameter(Name=awsenv[field])
      overrides[normalized_fields[field]] = response['Parameter']['Value']

  # add any remaining overrides from **kwargs
  for key, value in kwargs.items():
    overrides[key] = value

  return AppContext(**overrides)
