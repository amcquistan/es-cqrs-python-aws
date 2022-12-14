

from dataclasses import asdict
from typing import Dict, List

from boto3.dynamodb.conditions import Key

from availability.domain.event import Event
from availability.domain.model import Availability, UserAvailabilityAggregate
from availability.ports.repo import EventStoreRepo, AvailabilityRepo
from availability.utils.common import to_isodatetime, from_isodatetime


def event_from_ddb_item(item: Dict) -> Event:
  event_data = {}
  for k, v in item.items():
    if k == 'version':
      event_data[k] = int(v)
    elif k == "event_payload":
      event_data[k] = {
        "user_id": v["user_id"],
        "available_at": from_isodatetime(v["available_at"]),
        "appointment_id": v["appointment_id"]
      }
    else:
      event_data[k] = v
  return Event(**event_data)


def availability_to_ddb_item(availability: Availability) -> Dict:
  data = asdict(availability)
  return to_isodatetime(data)


def availability_from_ddb_item(item: Dict) -> Availability:
  return Availability(
    user_id=item['user_id'],
    available_at=from_isodatetime(item['available_at']),
    appointment_id=item["appointment_id"]
  )


class DynamoEventStoreRepo(EventStoreRepo):
  def __init__(self, table):
    self.table = table

  def fetch(self, user_id) -> UserAvailabilityAggregate:
    response = self.table.query(KeyConditionExpression=Key("user_id").eq(user_id))

    events = []
    for item in response['Items']:
      events.append(event_from_ddb_item(item))

    while 'LastEvaluatedKey' in response:
      last_key = response['LastEvaluatedKey']
      key_cond = (
        Key("user_id").eq(last_key['user_id']) &
        Key('version').gt(last_key['version'])
      )
      response = self.table.query(KeyConditionExpression=key_cond)
      for item in response['Items']:
        events.append(event_from_ddb_item(item))

    return UserAvailabilityAggregate(user_id=user_id, events=events)

  def save(self, event: Event):
    event_data = asdict(event)
    item = to_isodatetime(event_data)
    self.table.put_item(Item=item)


class DynamoAvailabilityRepo(AvailabilityRepo):
  def __init__(self, table):
    self.table = table

  def fetch(self, start, end=None, user_id=None) -> List[Availability]:
    key_cond = Key('available_at').gte(to_isodatetime(start))
    if end:
      key_cond = key_cond & Key('available_at').lt(to_isodatetime(end))

    if user_id:
      key_cond = key_cond & Key('user_id').eq(user_id)

    response = self.table.query(KeyConditionExpression=key_cond)
    availability = []
    for item in response['Items']:
      availability.append(availability_from_ddb_item(item))

    return availability


  def create(self, availability: Availability):
    item = availability_to_ddb_item(availability)
    self.table.put_item(Item=item)

  def update(self, availability: Availability):
    self.create(availability)

  def delete(self, availability: Availability):
    self.table.delete_item(Key={
      "user_id": availability.user_id,
      "available_at": to_isodatetime(availability.available_at)
    })
