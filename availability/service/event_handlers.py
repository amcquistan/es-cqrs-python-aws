import logging

from dataclasses import asdict
from datetime import datetime

from availability.domain import (
  Availability,
  Event,
  AvailabilityCreatedEvent,
  AvailabilityDeletedEvent,
  AppointmentAddedEvent,
  AppointmentRemovedEvent,
)

from availability.ports import AvailabilityRepo


log = logging.getLogger(__name__)


class AvailabilityEventHandler:
  def __init__(self, availability_repo: AvailabilityRepo):
    self.availability_repo = availability_repo

  def handle(self, event: Event):
    log.info(f'handling event {asdict(event)}')

    availability = Availability(**event.event_payload)
    if event.event_type == AvailabilityCreatedEvent.__name__:
      self.availability_repo.create(availability)

    elif event.event_type == AvailabilityDeletedEvent.__name__:
      self.availability_repo.delete(availability)

    elif event.event_type == AppointmentAddedEvent.__name__ or \
        event.event_type == AppointmentRemovedEvent.__name__:

      self.availability_repo.update(availability)

    else:
      log.warn(f"unknown event type {event.event_type}")


class AvailabilityQueryHandler:
  def __init__(self, availability_repo: AvailabilityRepo):
    self.availability_repo = availability_repo

  def handle(self, user_id: str = None, start: datetime = None, end: datetime = None):
    pass
