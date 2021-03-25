urls_to_zip
===========

A simple Python http microservice created with the [FastAPI](https://fastapi.tiangolo.com/) framework 
that loads a JSON data structure and responds with a .zip file whose 
contents are each of the source `url` named as `filename` within the 
final .zip archive. 

Sample data below:

```
[
  {
    "url": "https://media.giphy.com/media/3oz8xD0xvAJ5FCk7Di/giphy.gif",
    "filename": "pic001.gif"
  },
  {
    "url": "https://media.giphy.com/media/l3vRfhFD8hJCiP0uQ/giphy.gif",
    "filename": "pic002.gif"
  },
  ...
]
```

To Run:
-------
*Note: Written in Python 3.9.0*
- Clone the repo and change into the project directory:
```
git clone git@github.com:HarryLinux/urls_to_zip.git
cd urls_to_zip
```
- Create and activate your virtual environment:
```
python3 -m venv venv
source venv/bin/activate
```
- Install the requirements:
```
pip3 install -r requirements.txt
```
- Start the service:
```
uvicorn main:app
```

The server should now be running on `localhost:8000` (`http://127.0.0.1:8000`)

Endpoints
---------
The service exposes two endpoints, not including the auto-generated docs (Thanks FastAPI)
- POST `/get-zip`
  * Request body should contain a list of JSON objects like the one shown above
  * Given the data in the request body is valid, it will return a JSON response with status
  code `202` as shown below
```
{
  "message": "Zip file processing, send GET request to /get-zip/<zip_id>",
  "id": <zip_id>
}
```
   FastAPI provides a data validation system that can detect any invalid data type at the runtime  
   and returns the reason for bad inputs to the user in the JSON format.
- GET `/get-zip/{zip_id}`
  * Request should contain the `zip_id` returned from the POST request
  * If the zipping process has completed, the `FileResponse` object provided by FastAPI will asynchronously 
  stream the file as the response.
  * Else, you'll receive the appropriate JSON response with either status code `202` or `404` depending on 
  whether `zip_id` was valid and the process is pending, or the `zip_id` was invalid, respectively.

Testing
-------
To test the service you could use a client like [Insomnia](https://insomnia.rest/) or [Postman](https://www.postman.com/) 
using the enpoints and protocols mentioned earlier, passing in the appropriate parameters.

*or*

Using the CLI, you could send curl commands like shown below:

```
curl -X POST http://localhost:8000/get-zip -d '[{"url": "https://media.giphy.com/media/3oz8xD0xvAJ5FCk7Di/giphy.gif", "filename": "pic001.gif"}, {"url": "https://media.giphy.com/media/l3vRfhFD8hJCiP0uQ/giphy.gif", "filename": "pic002.gif"}]'

curl [-X GET] http://localhost:8000/get-zip/<zip_id> -o <output_file>.zip
```

Why FastAPI?
------------
This is a framework I've wanted to try out for a while now after reading about it, but 
[this article](https://www.analyticsvidhya.com/blog/2020/11/fastapi-the-right-replacement-for-flask/) does a great job highlighting 
the benefits and reasoning as to why FastAPI is a great choice over the more common Flask framework, or others for that matter.
