from typing import List

from datetime import datetime, timedelta

from availability.domain import Availability
from availability.ports import AvailabilityRepo


class AvailabilityQueryService:
  def __init__(self, availability_repo: AvailabilityRepo):
    self.availability_repo = availability_repo

  def fetch(self, user_id: str = None, start: datetime = None, end: datetime = None) -> List[Availability]:
    if not start:
      start = datetime.now() - timedelta(days=1)

    if not end:
      end = datetime.now() + timedelta(days=7)

    return self.availability_repo.fetch(start=start, end=end, user_id=user_id)
