
from abc import ABC, abstractmethod
from typing import List

from availability.domain.event import Event
from availability.domain.model import Availability, UserAvailabilityAggregate


class EventStoreRepo(ABC):
  @abstractmethod
  def fetch(self, user_id) -> UserAvailabilityAggregate:
    pass

  @abstractmethod
  def save(self, event: Event):
    pass


class AvailabilityRepo(ABC):
  @abstractmethod
  def fetch(self, start, end=None, user_id=None) -> List[Availability]:
    pass

  @abstractmethod
  def create(self, availability: Availability):
    pass

  @abstractmethod
  def delete(self, availability: Availability):
    pass
