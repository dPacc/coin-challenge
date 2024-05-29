# AIQ - Coin Challenge Backend

This project provides an API for detecting and segmenting circular objects in images. It allows users to upload images, process them to identify circular objects, and retrieve information about the detected objects.

## Table of Contents

- [AIQ - Coin Challenge Backend](#aiq---coin-challenge-backend)
  - [Table of Contents](#table-of-contents)
  - [Project Structure](#project-structure)
  - [API Endpoints](#api-endpoints)
    - [Upload Image](#upload-image)
    - [Get Images](#get-images)
    - [Get Image](#get-image)
    - [Process Image](#process-image)
    - [Delete Image](#delete-image)
    - [Get Objects](#get-objects)
    - [Get Object Details](#get-object-details)
  - [Models](#models)
    - [Image](#image)
    - [ObjectDetection](#objectdetection)
  - [Utility Functions](#utility-functions)
    - [Detection Algorithms](#detection-algorithms)
    - [Evaluation](#evaluation)
  - [Running the Backend](#running-the-backend)
  - [Containerization](#containerization)

## Project Structure

The project follows a modular structure to separate concerns and improve maintainability. Here's an overview of the project structure:

```
backend/
    |-- src/
    |   |-- models/
    |   |   |-- __init__.py
    |   |   |-- image.py
    |   |   |-- object_detection.py
    |   |
    |   |-- utils/
    |   |   |-- __init__.py
    |   |   |-- detection_algorithms.py
    |   |   |-- evaluation.py
    |   |
    |   |-- __init__.py
    |   |-- routes.py
    |
    |-- config.py
    |-- requirements.txt
    |-- Dockerfile
    |-- run.py
```

- The `app` package contains the Flask application.
- The `models` package inside `app` contains the database models.
- The `utils` package inside `app` contains utility functions for detection algorithms and evaluation.
- The `routes.py` file inside `app` contains the API routes.
- The `config.py` file contains the configuration settings for the application.
- The `requirements.txt` file lists the required dependencies.
- The `run.py` file is the entry point of the application.

## API Endpoints

### Upload Image

- Endpoint: `/upload`
- Method: POST
- Description: Uploads an image to the server and stores it in the database.
- Request: The image file should be sent as `multipart/form-data` with the key `image`.
- Response: Returns a JSON object containing the message and the ID of the uploaded image.

### Get Images

- Endpoint: `/images`
- Method: GET
- Description: Retrieves a list of all images stored in the database.
- Response: Returns a JSON array containing the details of each image, including the ID, filename, and base64-encoded image data.

### Get Image

- Endpoint: `/image/<image_id>`
- Method: GET
- Description: Retrieves a specific image by its ID.
- Parameters:
  - `image_id` (integer): The ID of the image to retrieve.
- Response: Returns a JSON object containing the ID, filename, and base64-encoded image data of the specified image.

### Process Image

- Endpoint: `/process/<image_id>`
- Method: POST
- Description: Processes an image to detect and segment circular objects.
- Parameters:
  - `image_id` (integer): The ID of the image to process.
- Request: The request body should contain a JSON object with the key `algorithm` specifying the detection algorithm to use (`manual`, `hough`, `threshold`, or `contour`).
- Response: Returns a JSON object containing the base64-encoded original image, image with bounding boxes, masked image, and the detected objects with their IDs, bounding boxes, centroids, and radii.

### Delete Image

- Endpoint: `/delete/<image_id>`
- Method: DELETE
- Description: Deletes a specific image and its associated object detections from the database.
- Parameters:
  - `image_id` (integer): The ID of the image to delete.
- Response: Returns a JSON object containing a success message if the image is deleted successfully.

### Get Objects

- Endpoint: `/objects/<image_id>`
- Method: GET
- Description: Retrieves a list of all circular objects detected in a specific image.
- Parameters:
  - `image_id` (integer): The ID of the image to retrieve objects from.
- Response: Returns a JSON array containing the details of each detected object, including the ID, bounding box, centroid, and radius.

### Get Object Details

- Endpoint: `/object/<object_id>`
- Method: GET
- Description: Retrieves the details of a specific circular object.
- Parameters:
  - `object_id` (string): The ID of the object to retrieve.
- Response: Returns a JSON object containing the ID, bounding box, centroid, and radius of the specified object.

## Models

### Image

The `Image` model represents an image stored in the database. It has the following attributes:

- `id` (integer): The unique identifier of the image.
- `filename` (string): The filename of the image.
- `data` (binary): The binary data of the image.

### ObjectDetection

The `ObjectDetection` model represents a detected circular object in an image. It has the following attributes:

- `id` (integer): The unique identifier of the object detection.
- `image_id` (integer): The ID of the associated image.
- `object_id` (string): The unique identifier of the object within the image.
- `bbox` (JSON): The bounding box coordinates of the object.
- `centroid` (JSON): The centroid coordinates of the object.
- `radius` (integer): The radius of the object.

## Utility Functions

### Detection Algorithms

The `detection_algorithms.py` file contains various functions for detecting and segmenting circular objects in an image:

- `manual_circle_mask`: Creates a circular mask based on manual annotations.
- `hough_circle_detection`: Detects circular objects using the Hough Circle Transform.
- `threshold_segmentation`: Segments circular objects using thresholding.
- `contour_based_segmentation`: Segments circular objects using contour detection.

### Evaluation

The `evaluation.py` file contains the `evaluate_model` function, which evaluates the performance of the object detection model on a given dataset. It calculates precision, recall, and F1 score based on the detected objects and ground truth annotations.

## Running the Backend

To run the backend locally, make sure you have Python and the required dependencies installed. Then, follow these steps:

1. Navigate to the `backend` directory.
2. Create a virtual environment (optional but recommended):

    ```
    python -m venv .env
    source .env/bin/activate
    ```

3. Install the dependencies:

    ```
    pip install -r requirements.txt
    ```

4. Set the necessary environment variables for the database connection.
5. Run the backend server:

    ```
    python app.py
    ```

    The backend server will start running at `http://localhost:8002`.

Alternatively, you can run the backend using Docker Compose as described in the project root directory's README.

## Containerization

The solution can be containerized using Docker. The `Dockerfile` in the project root directory defines the necessary steps to build the Docker image. The `docker-compose.yml` file can be used to orchestrate the containers, including the Flask application and the PostgreSQL database.

To build and run the containers, navigate to the project root directory and execute the following command:

```
docker-compose up --build
```

This will build the Docker images and start the containers. The API will be accessible at `http://localhost:8000`.
