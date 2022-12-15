from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List

from uuid import uuid4

from availability.domain.command import CreateAvailabilityCommand, DeleteAvailabilityCommand, AddAppointmentCommand, RemoveAppointmentCommand
from availability.domain.exception import AvailabilityExistsException, AvailabilityNotExistsException
from availability.domain.event import Event, AvailabilityCreatedEvent, AvailabilityDeletedEvent, AppointmentAddedEvent, AppointmentRemovedEvent


@dataclass(frozen=True)
class Availability:
  user_id: str
  available_at: datetime
  appointment_id: str


class UserAvailabilityAggregate:
  def __init__(self, user_id: str, start: datetime = None, events: List[Event] = None, version: int = 0):
    self.user_id = user_id
    self.start = start
    self.events = sorted(events or [], key=lambda e: e.created)
    self.uncommitted_events: List[Event] = []
    self.version = version

    self._availability: List[Availability] = []
    self.replay_events()

  def dict(self):
    return {
      "user_id": self.user_id,
      "start": self.start,
      "events": [asdict(e) for e in self.events],
      "uncommitted_events": [asdict(e) for e in self.uncommitted_events],
      "version": self.version,
      "availability": [asdict(a) for a in self.availability]
    }

  @property
  def availability(self) -> List[Availability]:
    return sorted(self._availability, key=lambda a:a.available_at)

  def replay_events(self):
    for event in self.events:
      self.user_id = event.user_id
      self.version = event.version
      data = event.event_payload
      common = {"correlation_id": event.correlation_id, "user_id": event.user_id, "available_at": data["available_at"]}
      if event.event_type == AvailabilityCreatedEvent.__name__:
        self.add_availability(CreateAvailabilityCommand(appointment_id=data["appointment_id"], **common))
      elif event.event_type == AvailabilityDeletedEvent.__name__:
        self.delete_availability(DeleteAvailabilityCommand(**common))
      elif event.event_type == AppointmentAddedEvent.__name__:
        self.add_appointment(AddAppointmentCommand(appointment_id=data["appointment_id"], **common))
      elif event.event_type == AppointmentRemovedEvent.__name__:
        self.remove_appointment(RemoveAppointmentCommand(**common))
    self.uncommitted_events.clear()

  def find_availability(self, available_at: datetime, raise_error=False):
    availability = None
    for a in self._availability:
      if a.available_at == available_at:
        availability = a
        break
    if not availability and raise_error:
      raise AvailabilityNotExistsException(f"Availability {available_at} does not exist for user {self.user_id}")

    return availability

  def add_availability(self, cmd: CreateAvailabilityCommand):
    availability = self.find_availability(cmd.available_at)
    if availability:
      raise AvailabilityExistsException(f"Availability {cmd.available_at} for user {self.user_id} exists already")

    availability = Availability(available_at=cmd.available_at, appointment_id=cmd.appointment_id, user_id=cmd.user_id)
    self._availability.append(availability)
    self.uncommitted_events.append(AvailabilityCreatedEvent(
      event_id=str(uuid4()),
      user_id=self.user_id,
      created=datetime.now(),
      event_type=AvailabilityCreatedEvent.__name__,
      event_payload=asdict(availability),
      correlation_id=cmd.correlation_id
    ))

    if self.start is None or self.start > cmd.available_at:
      self.start = cmd.available_at

    if availability.appointment_id:
      self.add_appointment(cmd)

  def delete_availability(self, cmd: DeleteAvailabilityCommand):
    availability = self.find_availability(cmd.available_at, raise_error=True)

    self._availability.remove(availability)
    self.uncommitted_events.append(AvailabilityDeletedEvent(
      event_id=str(uuid4()),
      user_id=self.user_id,
      created=datetime.now(),
      event_type=AvailabilityDeletedEvent.__name__,
      event_payload=asdict(availability),
      correlation_id=cmd.correlation_id
    ))

  def add_appointment(self, cmd: AddAppointmentCommand):
    orig_availability = self.find_availability(cmd.available_at, raise_error=True)
    i = self._availability.index(orig_availability)
    availability = Availability(available_at=cmd.available_at, appointment_id=cmd.appointment_id, user_id=cmd.user_id)
    self._availability[i] = availability

    self.uncommitted_events.append(AppointmentAddedEvent(
      event_id=str(uuid4()),
      user_id=self.user_id,
      created=datetime.now(),
      event_type=AppointmentAddedEvent.__name__,
      event_payload=asdict(availability),
      correlation_id=cmd.correlation_id
    ))

  def remove_appointment(self, cmd: RemoveAppointmentCommand):
    orig_availability = self.find_availability(cmd.available_at, raise_error=True)
    i = self._availability.index(orig_availability)
    availability = Availability(available_at=cmd.available_at, appointment_id=None, user_id=cmd.user_id)
    self._availability[i] = availability

    self.uncommitted_events.append(AppointmentRemovedEvent(
      event_id=str(uuid4()),
      user_id=self.user_id,
      created=datetime.now(),
      event_type=AppointmentRemovedEvent.__name__,
      event_payload=asdict(availability),
      correlation_id=cmd.correlation_id
    ))
