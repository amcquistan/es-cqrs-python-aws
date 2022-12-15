
from datetime import datetime
from typing import List, Union
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Header, Request, Response
from pydantic import BaseModel

from availability.config import configure
from availability.domain import Availability, CreateAvailabilityCommand, DeleteAvailabilityCommand, AddAppointmentCommand, RemoveAppointmentCommand
from availability.service import AvailabilityCommandHandler, AvailabilityQueryService


ctx = configure()
app = FastAPI()


class AvailabilityResponse(BaseModel):
  start: datetime
  end: datetime
  availability: List[Availability]


class AvailabilityRequest:
  available_at: datetime
  appointment_id: str = None


@app.middleware('http')
def ensure_correlation_id(request: Request, call_next):
  request.headers['x-correlation-id'] = request.headers.get('x-correlation-id', str(uuid4()))
  return call_next(request)


@app.get(f"{ctx.base_uri}/health")
async def health():
  return {"status": "up"}


@app.get(f"{ctx.base_uri}/availability", response_model=AvailabilityResponse)
def get_availability(
  start: Union[datetime, None] = None,
  end: Union[datetime, None] = None,
  user_id: Union[str, None] = None
):
  svc = AvailabilityQueryService(ctx.availability_repo)
  availability = svc.fetch(user_id=user_id, start=start, end=end)

  return AvailabilityResponse(
    start=start or min(availability, key=lambda a: a.available_at),
    end=end or max(availability, key=lambda a: a.available_at),
    availability=availability
  )


@app.post(f"{ctx.base_uri}/walker/<user_id>/availability", status_code=201)
def create_availability(
  user_id: str,
  request: AvailabilityRequest,
  correlation_id: str = Header(alias='x-correlation-id')
):
  handler = AvailabilityCommandHandler(user_id, ctx.event_store_repo)
  handler.add_availability(CreateAvailabilityCommand(
    correlation_id=correlation_id,
    user_id=user_id,
    available_at=request.available_at,
    appointment_id=request.appointment_id
  ))


@app.put(f"{ctx.base_uri}/walker/<user_id>/availability")
def update_availability(
  user_id: str,
  request: AvailabilityRequest,
  response: Response,
  correlation_id: str = Header(alias='x-correlation-id'),
):
  handler = AvailabilityCommandHandler(user_id, ctx.event_store_repo)

  availability = handler.aggregate.find_availability(available_at=request.available_at)
  if not availability.appointment_id and request.appointment_id is not None:
    handler.add_appointment(AddAppointmentCommand(
      correlation_id=correlation_id,
      user_id=user_id,
      available_at=request.available_at,
      appointment_id=request.appointment_id
    ))
  elif availability.appointment_id is not None and not request.appointment_id:
    handler.remove_appointment(RemoveAppointmentCommand(
      correlation_id=correlation_id,
      user_id=user_id,
      available_at=request.available_at,
      appointment_id=request.appointment_id
    ))
  else:
    # unsupported operation (bad request)
    response.status_code = 400


@app.delete(f"{ctx.base_uri}/walker/<user_id>/availability/<available_at>", status_code=204)
def delete_availability(
  user_id: str,
  available_at: datetime,
  correlation_id: str = Header(alias='x-correlation-id')
):
  handler = AvailabilityCommandHandler(user_id, ctx.event_store_repo)


if __name__ == '__main__':
  uvicorn.run(app, host='0.0.0.0', port=ctx.port, log_level=ctx.log_level)
