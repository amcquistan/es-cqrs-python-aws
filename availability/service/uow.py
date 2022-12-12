
from availability.domain.command import CreateAvailabilityCommand, DeleteAvailabilityCommand, AddAppointmentCommand, RemoveAppointmentCommand
from availability.ports import EventStoreRepo


class AvailabilityCommandHandler:
  def __init__(self, user_id: str, events_repo: EventStoreRepo):
    self.user_id = user_id
    self.events_repo = events_repo
    self.aggregate = events_repo.fetch(user_id)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, exc_tb):
    if exc_value is None:
      curr_version = self.aggregate.version + 1
      for event in self.aggregate.uncommitted_events:
        event.version = curr_version
        self.events_repo.save(event)
        self.aggregate.events.append(event)
        self.aggregate.version = curr_version
        curr_version += 1

      self.aggregate.uncommitted_events.clear()


  def add_availability(self, cmd: CreateAvailabilityCommand):
    self.aggregate.add_availability(cmd)

  def delete_availability(self, cmd: DeleteAvailabilityCommand):
    self.aggregate.delete_availability(cmd)

  def add_appointment(self, cmd: AddAppointmentCommand):
    self.aggregate.add_appointment(cmd)

  def remove_appointment(self, cmd: RemoveAppointmentCommand):
    self.aggregate.remove_appointment(cmd)
