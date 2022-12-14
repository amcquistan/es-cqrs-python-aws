import os

import boto3

from pydantic import BaseSettings

from availability.ports import AvailabilityRepo, EventStoreRepo
from availability.adapters import DynamoAvailabilityRepo, DynamoEventStoreRepo


class AppContext(BaseSettings):
  env: str = "local"
  port: int = 8000
  aws_region: str = "us-east-1"
  availability_event_store_table: str = "availability-event-store"
  availability_read_model_table: str = "availability-read-model"

  # This channel would be for events published and available for
  # consumption by other bounded contexts
  availability_channel: str = "availability"

  # This channel is for use within this apps bounded context and should not be exposed
  # to other bounded contexts because changes in event store schema would be immediately
  # felt by consumers in other bounded contexts. It is for capturing state change
  # events directly from the event store as in the via one of the following means:
  # - DynamoDB change data capture to Kinesis stream
  # - Published directly to via a producer in the app code after persisting to the event store 
  # - Published to as part of the outbox pattern
  availability_cdc_channel: str = "availability-cdc"

  # used to track progress of kinesis consumer via checkpoints saved to DynamoDB
  availability_consumer_table: str = "availability-consumer"

  # This would be for subscribing to state change events in another bounded context
  # responsible for the management of appointments
  appointments_channel: str = "appointments"

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

  @property
  def availability_repo(self) -> AvailabilityRepo:
    if "availability_repo" in self.cache:
      return self.cache["availability_repo"]

    ddb = boto3.resource('dynamodb', region_name=self.aws_region)
    self.cache["availability_repo"] = DynamoAvailabilityRepo(
      ddb.Table(self.availability_read_model_table)
    )
    return self.cache["availability_repo"]


def configure(**kwargs):
  """
  Initializes a configurable AppContext which provides settings and
  abstractions to key software architectural layer boundaries like
  repositories, messaging, http, and cli.
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
