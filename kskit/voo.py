import sys
import requests 
from requests.auth import HTTPBasicAuth 
import xmltodict
import json
import re
import pandas as pd
import numpy
from types import SimpleNamespace
import base64
from io import StringIO

def read_response(r):
  if r.status_code == 200 : 
    if re.search("xml|html", r.headers["content-type"]) != None :
      resp_dict=xmltodict.parse(r.text)
      return json.loads(json.dumps(resp_dict), object_hook=lambda d: SimpleNamespace(**d))
    elif re.search("json", r.headers["content-type"]) != None :
      return r.json(object_hook=lambda d: SimpleNamespace(**d))
    else :
      raise NotImplementedError(f"Handling content type { r.headers['content-type'] } is not supported @epi")
  else :
    raise ConnectionError(f"Got status {r.status_code}\n {r.text}")

def voo_parse(value, d_type):
  if value == None :
    return None
  elif d_type == "string":
    return str(value)
  elif d_type == "integer":
    return int(value)
  elif d_type == "primary_key":
    return int(value)
  elif d_type == "fkey_dico":
    return int(value)
  elif d_type == "fkey_varset":
    return int(value)
  elif d_type == "fkey_dico_ext":
    return str(value)
  elif d_type == False:
    return str(value)
  elif d_type == "date":
    if value == "0000-00-00":
      return None
    d = numpy.datetime64(value)
    return d if d.astype(object) <= pd.Timestamp.max.to_pydatetime().date() and d.astype(object) >= pd.Timestamp.min.to_pydatetime().date() else None
  elif d_type == "datetime":
    d = numpy.datetime64(value)
    return d if d.astype(object) <= pd.Timestamp.max.to_pydatetime() and d.astype(object) >= pd.Timestamp.min.to_pydatetime() else None
  else:
    raise NotImplementedError(f"Parsing {value} as {d_type} is not yet implemented")

def voo_type(columns):
  for (name, column) in columns.items():
    d_type = column.type
    if d_type == "string":
      yield (name, numpy.str)
    elif d_type == "integer":
      yield (name, "Int64")
    elif d_type == "primary_key":
      yield (name, "Int64")
    elif d_type == "fkey_dico":
      yield (name, "Int64")
    elif d_type == "fkey_varset":
      yield (name, "Int64")
    elif d_type == "fkey_dico_ext":
      yield (name, "string")
    elif d_type == False:
      yield (name, "string")
    elif d_type == "date":
      yield (name, numpy.datetime64)
    elif d_type == "datetime":
      yield (name, numpy.datetime64)
    else:
      raise NotImplementedError(f"Parsing type '{d_type}' is not yet implemented")

def generate_rows(rows, columns) : 
  for r in rows:
    yield [voo_parse(getattr(r, field), columns[field].type) for field in list(columns.keys())] 

def get_datasets(voo_url, login, password) :
  url = f'{voo_url}/ws/dataset'
  r = requests.get(url, auth = HTTPBasicAuth(login, password)) 
  ds = read_response(r)
  return ds.root.response.dataset

def get_dataset(voo_url, login, password, dataset, format = "json", order_by = None, batch = 500, folder = lambda new, cum: pd.concat([new, cum])) : 
  if type(dataset) == str and not dataset.isnumeric() :
    datasets = list(line.id for line in get_datasets(voo_url, login, password) if line.name == dataset)
    if len(datasets) == 0:
      print(f"Cannot find data Query {dataset}")
      return
    else:
      dataset = datasets[-1] 
  lines = 0
  sort = "/sort/"+order_by if order_by != None else "" 
  next_url = f'{voo_url}/ws/dataset/id/{dataset}/format/{format}{sort}/begin/0/range/{batch}' 
  page = 1
  folded_df = None
  while next_url != None:
    #print(next_url)
    r = read_response(requests.get(next_url, auth = HTTPBasicAuth(login, password))) 
    next_url = None
    new_df = None
    if format == "csv" :
      filemame = r.root.response.filename
      chunks = int(r.root.response.total_chunks)
      csv_string = StringIO(base64.b64decode(r.root.response.content.encode("ascii")).decode("UTF-8"))
      new_df = pd.read_csv(csv_string, sep=";")
      if chunks > page:
        next_url = f'{voo_url}/ws/dataset/id/{dataset}/format/{format}{sort}/filename/{filename}/chunk_index/{page + 1}' 
      else: 
        next_url = None
    elif format == "json": 
      total_rows = int(r.total_rows)
      begin = int(r.begin)
      range = int(r.range)
      columns = dict([(n, getattr(r.metadata.fields,n )) for n in dir(r.metadata.fields) if re.match("^__", n) == None])
      data = generate_rows(r.rowdata, columns)
      new_df = pd.DataFrame(data = data, columns = columns.keys()).astype(dict(voo_type(columns)))
      lines = lines + new_df.shape[0]
      print(f"{lines} of {r.total_rows}", end="\r", flush=True)
      if begin + new_df.shape[0] >= total_rows:
        next_url = None
      elif begin != (page - 1) * range:
        raise ValueError(f"Cannot iterate in data query. 'begin' should not be {begin} on page {page} if range is {range}")
      else: 
        next_url = f'{voo_url}/ws/dataset/id/{dataset}/format/{format}{sort}/begin/{begin + new_df.shape[0]}/range/{batch}'
    else: 
      raise ValueError(f"Requesting dataqueries on format {format} is not implemented")

    page = page + 1
    folded_df = folder(new_df, folded_df)
  return folded_df
    
