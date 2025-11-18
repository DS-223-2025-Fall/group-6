
# EdRetain Dashboard - Frontend

Welcome to the **Frontend** of the **EdRetain Dashboard**, part of the **Marketing Analytics** group project. This application is built using **Streamlit** and provides an interactive UI for visualizing retention data, learner engagement, churn predictions, and campaign performance.

The project is containerized using **Docker**, and can be run both locally or inside a Docker container for ease of deployment.

## Project Structure

```bash
frontend/
│
├── app.py              # Main Streamlit application (UI skeleton)
├── requirements.txt    # List of Python dependencies required for the app
└── Dockerfile          # Docker container configuration for frontend service
```

### Key Files

- **`app.py`**: This file contains the core of the frontend application, including all UI elements and logic for rendering charts, tables, and data visualizations. It leverages Streamlit's powerful features to provide a clean and interactive user experience.
  
- **`requirements.txt`**: This file lists all the Python dependencies needed to run the frontend application. It ensures that the right versions of libraries are installed, making the app environment reproducible.

- **`Dockerfile`**: The configuration file for creating a Docker image to run the Streamlit app in a container. This helps with the deployment and ensures the environment is consistent across all setups.

---

## Running the Frontend

### 1. Run Locally (Without Docker)

If you prefer to run the app locally without Docker, follow the steps below:

#### Prerequisites

Make sure you have **Python 3.10+** installed on your local machine. If not, please download and install the latest version of Python.

#### Steps

1. **Navigate to the `frontend` directory**:

   ```bash
   cd frontend
   ```

2. **Install the required dependencies**:

   This will install all the necessary libraries from the `requirements.txt` file:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit app**:

   Finally, run the application:

   ```bash
   streamlit run app.py
   ```

   After running the command, the Streamlit app will open in your default browser at `http://localhost:8501`.

### 2. Running with Docker

Running the frontend in a **Docker container** ensures that the environment is the same regardless of where the app is deployed. If you're unfamiliar with Docker, here's a quick guide to get started:

#### Build the Docker Image

From the root of the project directory, build the Docker image for the frontend service using the following command:

```bash
docker build -t frontend-service ./frontend
```

This will create a Docker image named `frontend-service`.

#### Run the Docker Container

After the image is built, you can run the app in a container using this command:

```bash
docker run --rm -p 8501:8501 frontend-service
```

This command tells Docker to map port `8501` inside the container to port `8501` on your local machine. Once the container is running, you can access the app at `http://localhost:8501`.

---

## Dockerfile Overview

The Dockerfile defines the configuration for the containerized environment. Below is a summary of what the Dockerfile does:

- **Base Image**: Uses `python:3.11-slim` as the base image, providing a minimal Python environment to keep the image size small.
  
- **Dependencies**: Installs all necessary Python libraries by reading the `requirements.txt` file, ensuring the app has all the required dependencies.

- **App Setup**: Copies the Streamlit application (`app.py`) into the `/app` directory of the container.

- **Port**: The app runs on port `8501`, which is exposed and mapped to the host machine so that you can interact with the Streamlit UI.

---

## Troubleshooting

- **Streamlit Issues**: If you're encountering issues with Streamlit not displaying or running as expected, make sure all dependencies are correctly installed and try restarting the app.

- **Docker Issues**: If you're running into problems with Docker, ensure that Docker is properly installed on your machine. Check the Docker documentation for installation guides.

---

