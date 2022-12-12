from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
  event_id: str
  user_id: str
  created: datetime
  event_type: str
  event_payload: dict
  correlation_id: str
  version: int = 0


@dataclass
class AvailabilityCreatedEvent(Event):
  pass


@dataclass
class AvailabilityDeletedEvent(Event):
  pass


@dataclass
class AppointmentAddedEvent(Event):
  pass


@dataclass
class AppointmentRemovedEvent(Event):
  pass
