"""
Run as a module from the shell.

Examples:

  python -m availability.adapters.cli seed

  python -m availability.adapters.cli show-aggregate --user-id abc123
"""

import json

from argparse import ArgumentParser
from datetime import datetime, timedelta
from uuid import uuid4

from availability.config import AppContext, configure
from availability.domain import (
  CreateAvailabilityCommand,
  DeleteAvailabilityCommand,
  AddAppointmentCommand,
  RemoveAppointmentCommand,
  UserAvailabilityAggregate
)
from availability.service import AvailabilityCommandHandler
from availability.utils import to_isodatetime, from_isodatetime

from availability.adapters.event_processor import process_availability_events
from availability.adapters.restapi import app


def seed(ctx: AppContext):
  user_id1, user_id2 = "abc456", "qrs789"
  user_n1, user_n2 = 5, 2

  now = datetime.now()
  start = datetime(now.year, now.month, now.day, now.hour)

  handler1 = AvailabilityCommandHandler(
    user_id=user_id1,
    events_repo=ctx.event_store_repo
  )
  handler2 = AvailabilityCommandHandler(
    user_id=user_id2,
    events_repo=ctx.event_store_repo
  )

  for i in range(1, max(user_n1, user_n2)):
    start += timedelta(hours=i)
    if i <= user_n1:
      with handler1:
        handler1.add_availability(CreateAvailabilityCommand(
          correlation_id=str(uuid4()),
          user_id=user_id1,
          available_at=start,
        ))

    if i <= user_n2:
      with handler2:
        handler2.add_availability(CreateAvailabilityCommand(
          correlation_id=str(uuid4()),
          user_id=user_id2,
          available_at=start,
        ))


def print_aggregate(aggregate: UserAvailabilityAggregate):
  aggregate = to_isodatetime(aggregate.dict())
  print(json.dumps(aggregate, indent=2))


def show_aggregate(ctx: AppContext, user_id: str):
  handler = AvailabilityCommandHandler(
    user_id=user_id,
    events_repo=ctx.event_store_repo
  )
  print_aggregate(handler.aggregate)


def delete_availability(ctx: AppContext, user_id: str, available_at: str):
  handler = AvailabilityCommandHandler(
    user_id=user_id,
    events_repo=ctx.event_store_repo
  )
  with handler:
    handler.delete_availability(DeleteAvailabilityCommand(
      correlation_id=str(uuid4()),
      user_id=user_id,
      available_at=from_isodatetime(available_at)
    ))
  print_aggregate(handler.aggregate)


def add_appointment(ctx: AppContext, user_id: str, available_at: str, appointment_id: str):
  handler = AvailabilityCommandHandler(
    user_id=user_id,
    events_repo=ctx.event_store_repo
  )
  with handler:
    handler.add_appointment(AddAppointmentCommand(
      correlation_id=str(uuid4()),
      user_id=user_id,
      available_at=from_isodatetime(available_at),
      appointment_id=appointment_id
    ))
    print_aggregate(handler.aggregate)


if __name__ == '__main__':
  parser = ArgumentParser(
    "python -m availability.adapters.cli",
    description="Gives ability to drive this service from terminal by specifying one of the positional arguments as an operation followed by options where appropriate."
  )

  SEED = 'seed'
  CREATE_AVAILABILITY = 'create-availability'
  DELETE_AVAILABILITY = 'delete-availability'
  ADD_APPOINTMENT = 'add-appointment'
  REMOVE_APPOINTMENT = 'remove-appointment'
  SHOW_AGGREGATE = 'show-aggregate'
  PROCESS_AVAILABILITY_EVENTS = 'process-availability-events'

  parser.add_argument('op', choices=[
    SEED,
    CREATE_AVAILABILITY,
    DELETE_AVAILABILITY,
    ADD_APPOINTMENT,
    REMOVE_APPOINTMENT,
    SHOW_AGGREGATE,
  ])

  parser.add_argument('--user-id')
  parser.add_argument('--available-at')
  parser.add_argument('--appointment-id')

  args = parser.parse_args()

  ctx = configure()

  if args.op == SEED:
    seed(ctx)
  elif args.op == SHOW_AGGREGATE:
    show_aggregate(ctx, args.user_id)
  elif args.op == DELETE_AVAILABILITY:
    delete_availability(ctx, args.user_id, args.available_at)
  elif args.op == ADD_APPOINTMENT:
    add_appointment(ctx, args.user_id, args.available_at, args.appointment_id)
