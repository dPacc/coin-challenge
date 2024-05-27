# AIQ - Coin Challenge Frontend

The frontend of the AIQ - Coin Challenge application provides a user interface to upload images, process them to detect and segment circular objects, and visualize the results. It is built using React and utilizes Ant Design components for the user interface.

## Table of Contents

- [AIQ - Coin Challenge Frontend](#aiq---coin-challenge-frontend)
  - [Table of Contents](#table-of-contents)
  - [Project Structure](#project-structure)
  - [User Interface](#user-interface)
  - [Styling and UI Components](#styling-and-ui-components)
  - [Routing](#routing)
  - [Running the Frontend](#running-the-frontend)
  - [Deployment](#deployment)

## Project Structure

The frontend directory is organized as follows:

```
frontend/
|-- src/
|   |-- components/
|   |   |-- ImageUpload.js
|   |   |-- ImageList.js
|   |
|   |-- App.js
|   |-- index.js
|
|-- public/
|   |-- index.html
|   |-- favicon.ico
|   |-- manifest.json
|
|-- package.json
|-- README.md
```

- The `src` directory contains the source code for the frontend.
  - The `components` directory contains reusable React components.
    - `ImageUpload.js`: Implements the image upload functionality.
    - `ImageList.js`: Displays the list of uploaded images and their processing status.
  - `App.js`: The main component that sets up the routing and layout of the application.
  - `index.js`: The entry point of the frontend application.
- The `public` directory contains the public assets and the HTML template.
- `package.json`: Lists the dependencies and scripts for the frontend.

## User Interface

The frontend provides a user-friendly interface with the following components:

- Image Upload: Allows users to upload images for processing. The uploaded images are sent to the backend API for detection and segmentation of circular objects.
- Image List: Displays a list of uploaded images along with their processing status. Users can view the original image, the image with bounding boxes around the detected objects, and the masked image highlighting the segmented objects.

The frontend communicates with the backend API to upload images, initiate the processing, and retrieve the results. It sends requests to the appropriate API endpoints and handles the responses to update the user interface accordingly.

## Styling and UI Components

The frontend uses Ant Design, a popular React UI library, for styling and pre-built UI components. The Ant Design components provide a consistent and visually appealing user interface.

## Routing

The frontend uses React Router for handling navigation between different pages. The main routes are defined in the `App.js` component:

- `/`: The home page that displays the image upload component and the list of uploaded images.
- `/images`: The page that displays the list of all uploaded and processed images, details of a specific image, including the original image, image with bounding boxes, and masked image can be got by clicking on them.

## Running the Frontend

To run the frontend locally, make sure you have Node.js and the required dependencies installed. Then, follow these steps:

1. Navigate to the `frontend` directory.
2. Install the dependencies:

   ```
   npm install
   ```

3. Run the frontend development server:

   ```
   npm start
   ```

   The frontend will start running at `http://localhost:3000`.

## Deployment

To deploy the frontend for production, you can build the optimized production-ready version of the frontend using the following command:

```
npm run build
```

This will generate a `build` directory containing the production-ready files. You can then serve the contents of the `build` directory using a static file server or deploy it to a hosting platform of your choice.
