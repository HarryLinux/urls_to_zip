from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from zipfile import ZipFile, ZIP_DEFLATED
from fastapi.responses import FileResponse, JSONResponse
from tempfile import TemporaryDirectory
from uuid import uuid4
import os
import asyncio
import aiohttp
import aiofiles


# Data Model for the POST request body items
class URLData(BaseModel):
  url: str
  filename: str

app = FastAPI()

# Dict to check status of task (key: zip_id, val: 'pending' | 'complete')
# Task entry deleted after returning zip to client
task_dict = {}

# This async func takes the list from the request body and a temp dir to store the files;
# fetching each asynchronously with fetch_file() and ensuring unique 
# filenames with get_filename_to_arc() then returns the files 
async def loop_session_calls(urls: list[URLData], tmpdir: TemporaryDirectory):
  # file name dict to be consumed by get_filename_to_arc() then reset
  file_name_dict = {}

  def get_filename_to_arc(item: URLData) -> str:
    try:
      # if file name exists in dict: 
      # modify filename appending (value) before the extension
      if file_name_dict[item.filename]:
        new_filename = item.filename[:item.filename.index('.')] \
          + f'({file_name_dict[item.filename]})' \
          + item.filename[item.filename.index('.'):]

        # then increment the value assigned
        file_name_dict[item.filename] += 1
        return new_filename

    except KeyError:
      # else initialize dict entry as 1
      file_name_dict[item.filename] = 1
      return item.filename


  async def fetch_file(session, item: URLData):
    try:
      async with session.get(item.url) as res:
        filename_to_arc = get_filename_to_arc(item)
        file_contents = await res.content.read()

        async with aiofiles.open(f'{tmpdir.name}/{filename_to_arc}', 'wb') as file_to_arc:

          await file_to_arc.write(file_contents)
          print(f'wrote the content to a file for {item.url}')
          return file_to_arc

    except aiohttp.ClientConnectorError as e:
      print(f'There has been a connection error: {e}')
      return {
        'item': item,
        'error': e,
      }
    except Exception as ex:
      print(f'Unexpected issue: {ex}')
      return {
        'item': item,
        'error': ex,
      }

  # Fire off all the async fetch_file() calls for each item in the request body
  # Return the files listed in a temp directory
  async with aiohttp.ClientSession() as session:
    tasks = [fetch_file(session, item) for item in urls]
    file_list = await asyncio.gather(*tasks)

    # reset file name dict and return file_list
    file_name_dict = {}
    return file_list


# Get the list of files from loop_session_calls() passing in the urls from the 
# POST request body and write them to a zip file, currently skipping the files that
# weren't successfully retrieved, could do something else in the future 
async def create_zipfile(urls: list[URLData], tmpdir: TemporaryDirectory, zip_id: str):
  file_list = await loop_session_calls(urls, tmpdir)

  def zip_files(file_list: list) -> str:
    file_path = f'./{zip_id}.zip'

    try:
      with ZipFile(file_path, 'w', compression=ZIP_DEFLATED) as myzip:
        for f in file_list:
          if type(f) == dict and 'error' in f.keys():
            print(f"URL: {f['item'].url} failed with error: {f['error']}")
            continue

          elif f:
            name_to_save = f.name.split('/')[-1]
            # append to the zip archive
            myzip.write(f.name, arcname=name_to_save)
            print(f'wrote {name_to_save} to myzip')
          else:
            print('There has been an issue...f==None')
    except Exception as e:
      print(f'An unrealized exception: {e}')

  zip_files(file_list)


async def getzip(urls: list[URLData], zip_id: str):
  # temp directory to save fetched files
  tmpdir = TemporaryDirectory()
  file_path = await create_zipfile(urls, tmpdir, zip_id)
  # Change task status to 'complete' in task_dict
  task_dict[zip_id] = 'complete'


def delete_zip(file_path: str):
  try:
    os.remove(file_path)
  except Exception as e:
    print(f'An unrealized exception: {e}')


# Return the zip to client if task is completed, then kickoff 
# background task to delete the zip after returning
# Send appropriate response otherwise
@app.get('/get-zip/{zip_id}')
async def retrieve_zip(zip_id: str, background_tasks: BackgroundTasks):
  file_path = f'./{zip_id}.zip'

  try:
    if task_dict[zip_id] == 'complete' and os.path.exists(file_path):
      del task_dict[zip_id]
      background_tasks.add_task(delete_zip, file_path)
      return FileResponse(file_path, \
        media_type='application/x-zip-compressed', \
          filename=file_path, \
            status_code=200)
    else:
      return JSONResponse({
        'message': 'Zip file still processing, try again',
        'id': zip_id
        }, status_code=202)
  except KeyError:
    return JSONResponse({
      'message': 'This zip id is invalid or has already been returned',
      'id': zip_id
      }, status_code=404)


# Generate task/zip id, set status to pending in task_dict and fireoff 
# background task to start the zipping process after responding to the request
@app.post('/get-zip')
async def main(urls: list[URLData], background_tasks: BackgroundTasks):
  zip_id = str(uuid4())
  task_dict[zip_id] = 'pending'
  background_tasks.add_task(getzip, urls, zip_id)
  return JSONResponse({
    'message': 'Zip file processing, send GET request to /get-zip/<zip_id>',
    'id': zip_id
    }, status_code=202)
