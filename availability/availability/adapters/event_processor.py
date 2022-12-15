import json
import platform
import logging
import multiprocessing

from kinesis.consumer import KinesisConsumer
from kinesis.state import DynamoDB

from availability.config import AppContext, configure
from availability.domain import Event
from availability.service import AvailabilityEventHandler
from availability.utils import from_isodatetime


log = logging.getLogger(__name__)
# logging.basicConfig()
# logging.getLogger('kinesis.consumer').setLevel(logging.DEBUG)

def process_availability_events(ctx: AppContext):
  log.info('initiating availability event processing')
  handler = AvailabilityEventHandler(ctx.availability_repo)

  consumer = KinesisConsumer(
    stream_name=ctx.availability_cdc_channel,
    state=DynamoDB(table_name=ctx.availability_consumer_table)
  )

  for message in consumer:
    log.info(f"received message {message}")
    event = cdc_message_to_event(message)
    handler.handle(event)


def cdc_message_to_event(message) -> Event:
  """
  message parameter comes in with the following format

  {'SequenceNumber': '49636080407048354368315237172905799799558406021643763714',
   'ApproximateArrivalTimestamp': datetime.datetime(2022, 12, 13, 17, 33, 2, 278000, tzinfo=tzlocal()),
   'Data': b'{"awsRegion":"us-east-1","eventID":"274830c0-ea7b-433c-9ce3-a5de1ae9363e","eventName":"INSERT","userIdentity":null,"recordFormat":"application/json","tableName":"availability-event-store","dynamodb":{"ApproximateCreationDateTime":1670974381510,"Keys":{"version":{"N":"1"},"user_id":{"S":"abc123"}},"NewImage":{"event_payload":{"M":{"user_id":{"S":"abc123"},"appointment_id":{"NULL":true},"available_at":{"S":"2022-12-13T18:00:00"}}},"event_type":{"S":"AvailabilityCreatedEvent"},"version":{"N":"1"},"user_id":{"S":"abc123"},"correlation_id":{"S":"eb001879-191e-4599-9b23-696a89138f2b"},"created":{"S":"2022-12-13T17:33:01.310159"},"event_id":{"S":"0c692c83-a085-494a-9294-6b2bf9b66df7"}},"SizeBytes":283},"eventSource":"aws:dynamodb"}',
   'PartitionKey': '03E27A99AD41451219A4D9629E53091C',
   'EncryptionType': 'KMS'}
  """
  event_data = json.loads(message['Data'].decode('utf-8'))\
    .get('dynamodb')\
    .get('NewImage')

  event_payload = event_data['event_payload']['M']

  return Event(
    event_id=event_data['event_id']['S'],
    user_id=event_data['user_id']['S'],
    created=from_isodatetime(event_data['created']['S']),
    event_type=event_data['event_type']['S'],
    event_payload={
      'user_id': event_payload['user_id']['S'],
      'appointment_id': event_payload['appointment_id'].get('S'),
      'available_at': from_isodatetime(event_payload['available_at']['S'])
    },
    correlation_id=event_data['correlation_id']['S'],
    version=int(event_data['version']['N'])
  )


if __name__ == '__main__':
  ctx = configure()

  # work around required due to Mac OS process management issue
  # https://github.com/borgstrom/offspring/issues/4
  # https://github.com/NerdWalletOSS/kinesis-python/issues/14
  if platform.system() == 'Darwin':
    multiprocessing.set_start_method("fork")

  process_availability_events(ctx)
