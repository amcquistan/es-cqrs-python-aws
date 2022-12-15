
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Union


def to_isodatetime(data: Union[dict, datetime]) -> Union[dict,str]:
    if isinstance(data, dict):
      item = {}
      for k, v in data.items():
        if isinstance(v, datetime) or isinstance(v, dict):
          v = to_isodatetime(v)
        elif isinstance(v, list):
          v = [to_isodatetime(x) for x in v]
        item[k] = v
      return item
    elif isinstance(data, datetime):
      return data.isoformat()


def from_isodatetime(dt: str) -> datetime:
  return datetime.fromisoformat(dt)
