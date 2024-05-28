# AIQ - Coin Challenge

This project is a full-stack application for detecting and segmenting circular objects in images. It consists of a backend API built with Flask and a frontend user interface built with React.

## Table of Contents

- [AIQ - Coin Challenge](#aiq---coin-challenge)
  - [Table of Contents](#table-of-contents)
  - [Architecture](#architecture)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
  - [Usage](#usage)
  - [Containerization](#containerization)

## Architecture

The application follows a client-server architecture, with the backend serving as an API and the frontend consuming the API to provide a user interface. The architecture can be represented as follows:

```
+-------------------+
|     Frontend      |
|   (React App)     |
+-------------------+
|
| HTTP Requests
|
+-------------------+
|     Backend       |
|   (Flask API)     |
+-------------------+
|
| Database Queries
|
+-------------------+
|     Database      |
|    (PostgreSQL)   |
+-------------------+
```

The backend API is built using Flask and handles image upload, processing, and retrieval. It communicates with a PostgreSQL database to store and retrieve image and object detection data. The frontend, built with React, provides a user-friendly interface for interacting with the backend API.

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Installation

1. Clone the repository:

2. Navigate to the project root directory:

3. Build and start the containers:

```
docker-compose up --build
```

This will build the Docker images and start the containers for the backend, frontend, and database.

## Usage

Once the containers are up and running, you can access the application through the following URLs:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Adminer (Database Management): `http://localhost:8082`

The frontend provides a user interface for uploading images, processing them to detect circular objects, and visualizing the results. The backend API can be accessed directly for programmatic interaction.

## Containerization

The application is containerized using Docker and Docker Compose. The `docker-compose.yml` file defines the services and their configurations. It includes the backend, frontend, and database services, along with an Adminer service for database management.

To build and run the containers, navigate to the project root directory and execute the following command:
