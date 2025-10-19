# Search Engine

## Overview
This project is a search engine for ancient Greek and Latin texts. It is containerized with [Docker Compose](https://docs.docker.com/compose/) for easy deployment and setup, and exposes REST APIs over HTTP for queries and other operations.

## Setup Instructions

### Prerequisites
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- (Optional) [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) for GPU acceleration

**Note:** GPU acceleration is optional. Without it, the system will fall back to CPU processing, resulting in significantly longer indexing times.

### System Requirements
- Tested on: Ubuntu 24.04 LTS
- Recommended: 16 GB RAM, NVIDIA 1080 Ti GPU

Lower-spec systems are supported by:
- Adjusting ElasticSearch memory settings (see [docker-compose.yml](docker-compose.yml)).
- Removing the `deploy.resources.reservations.devices` section from the web service to disable GPU acceleration.

### Installation
1. Build the Docker images:
   ```bash
   docker compose build
   ```
2. (Optional) Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) for faster embedding computations during indexing and querying.

3. Start the containers:
    ```bash
    docker compose up -d
    ```

4. Access the web interface at [http://localhost:8000](http://localhost:8000)

### Project Components
This project leverages an [elasticsearch image](https://hub.docker.com/_/elasticsearch) enriched with a custom layer (for plugin installation), a standard [postgres image](https://hub.docker.com/_/postgres) and a custom [python image](https://hub.docker.com/_/python) to iplement the HTTP backend and the diagnostic web interface. The `elasticsearch/` and `postgres/` folders are used by Docker for data persistence and should be left untouched. See [docker-compose.yml](docker-compose.yml) for details.


## Usage

### Creating Indices
Before indexing data, an index for the language must be created. This can be achieved by issuing a POST request to `/api/indices/<language>`:
```bash
curl -X POST localhost:8000/api/indices/greek
```
or by using the [development web interface](http://localhost:8000/admin). This will create an empty index with the necessary configuration and analyzers.


### Indexing Datasets
This project comes without any dataset, which must be provided by uses. Datasets must be copied into `assets/dataset/<language>/` folders (supported languages are `greek` and `latin`), and must be in the following JSON format as a list of documents:
```json
[
  {
    "id": "gottingen.genesis.1.1",  # Unique identifier, preferably in the form source.book.chapter.id
    "type": "biblical-verse",       # Type of document, currenlty only biblical-verse is supported
    "source": "gottingen",          # Author, edition, manuscript, etc.
    "book": "genesis",              # Book title
    "chapter": "1",                 # Chapter
    "verse": "1",                   # Verse
    "content": "Ἐν ἀρχῇ ἐποίησεν ὁ θεὸς τὸν οὐρανὸν καὶ τὴν γῆν.",  # Textual content of the document
    "variant": [                    # List of historically attested variants of this document
      {
        "source": "G_α",            # Author, edition, manuscript, etc. of this variant
        "content": "ἐν κεφαλαίῳ ἔκτισεν σὺν τὴν γῆν."   # Textual content of this variant
      },
      ...
    ]
  },
  ...
]
```
Once data has been placed in the correct folder, it can be indexed by issuing a `POST` request to `/api/data/<language>/<dataset-name>`, for instance:
```bash
curl -X POST http://localhost:8000/api/data/greek/gottingen
```
or by using the [development web interface](http://localhost:8000/admin).


### Running a Query
Queries can be issued by sending a `POST` request to `/api/search/<language>`. For the list of accepted parameters see [search.py](webapp/app/api/search.py). A simple example for searching the text "Ἐν ἀρχῇ ἐποίησεν ὁ θεὸς":
```bash
curl -X POST http://localhost:8000/api/search/greek -H "Content-Type: application/json" -d '{"query":"Ἐν ἀρχῇ ἐποίησεν ὁ θεὸς"'
```
It is also possible to run a query and set configuration parameters by using the [development web interface](http://localhost:8000).


## Test Cases and Collections

Through the [development web interface](http://localhost:8000), you can configure test cases and organize them into collections for automated testing.

### Test Cases
A test case defines:
- A citing passage (`source`, `content`, and optionally the full textual `context` from which `content` was taken)
- A `language`
- A `target` passage (e.g., `gottingen.genesis.1.1`)

Optionally, tags can be associated with test cases for easier filtering. Test cases can be managed through the [Test Cases interface](http://localhost:8000/test-cases).

### Test Collections
A test collection is a group of test cases combined with a search configuration. This configuration may include:
- Filters on `sources` or `books`
- Specific `weights` for the search engine
- Other search parameters

Collections can be configured from the [Test Collections interface](http://localhost:8000/test-collections).

### Running Test Collections
A test collection can be executed to generate a **result collection**, which includes:
- Retrieved results for each configured test case
- Statistics such as Recall@K and Mean Reciprocal Rank (MRR)
- Individual result cases accessible via the result collection detail page

Both result collections and individual result cases allow comments.

### API Access
Test cases and collections are also accessible through the API system. For more details, see the [`webapp/app/api/`](webapp/app/api/) directory.