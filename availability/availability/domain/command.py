
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Command:
  correlation_id: str
  user_id: str
  available_at: datetime


@dataclass
class CreateAvailabilityCommand(Command):
  appointment_id: str = None


@dataclass
class AddAppointmentCommand(Command):
  appointment_id: str


@dataclass
class RemoveAppointmentCommand(Command):
  pass


@dataclass
class DeleteAvailabilityCommand(Command):
  pass
