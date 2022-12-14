# digit_recognition

- [Code](../../services/digit_recognition)
- digit_recognition URL when run locally: <http://localhost:8383/docs>
- digit_recognition URL when deployed on Fribourg's Kubernetes: <https://digit-recognition-csia-pme.kube.isc.heia-fr.ch/docs>

## Description

This service uses a keras model to guess a digit in an image.

The service is built in two steps:

1. [Model creation](#model-creation) - The creation of the model from the data
2. [Model serving](#model-serving) - The serving of the built model

## Model creation

The goal of this step is to prepare the data and train a new model. All further commands are ran in the [model_creation](../../services/digit_recognition/model_creation) directory.

### Run the experiment

The model can be tweaked using the [`params.yaml`](../../services/digit_recognition/model_creation/params.yaml) file. The `numbers` parameter allows to indicate the digits the model must be able to detect.

Run a new training using the following commands.

```sh
# Export the MinIO S3 credentials (ask them to other members of the team)
export AWS_ACCESS_KEY_ID=***
export AWS_SECRET_ACCESS_KEY=***

# Pull the required data for the experiment from MinIO
dvc pull

# Reproduce the ML experiment with DVC
dvc repro
```

The DVC pipeline is described in the [`dvc.yaml`](../../services/digit_recognition/model_creation/dvc.yaml) file.

Each stage describes the dependencies and the outputs of the stage. Every time a dependency of the experiment is updated, running `dvc repro` will run the stages of the pipeline that are affected and keep the results in cache to speed up future runs.

More information on their website: [_Get Started: Data Pipelines_ - dvc.org](https://dvc.org/doc/start/data-management/data-pipelines).

### Push new data/results to MinIO

In order to push new results to MinIO, use the following commands (similar to Git). **Note**: DVC automatically adds files that are specified in the pipelines. In other words, there are no needs to explicitely add those files with `dvc add`.

```sh
# Get the data status
dvc status

# Add the required files to DVC
dvc add <the files you would add to DVC>

# Push the data to DVC
dvc push
```

## Model serving

The goal of this step is to serve the model made in the previous step. All further commands are ran in the [model_serving](../../services/digit_recognition/model_serving) directory.

The API documentation is automatically generated by FastAPI using the OpenAPI standard. A user friendly interface provided by Swagger is available under the `/docs` route, where the endpoints of teh service are described.

This simple service only has one route `/compute` that takes an image as input, which will be used to guess the number.

### Retrieve the model

Run the following command to get the model created from the previous step.

```sh
# Copy the model from the creation directory
cp ../model_creation/mnist_model.h5 .
```

### How to run

#### Environment variables

The service will use the following environment variables if defined.

*General variables*

- `APP_HOST`: address on which the API will listen, default is 127.0.0.1
- `APP_PORT`: port the API will listen on, default is 8080
- `APP_LOG`: log level, default is info
- `APP_ENGINE`: the url to the engine, if provided, the service will announce itself to the engine periodically
- `APP_SERVICE`: the url of the service itself, needed to announce correct routes to the engine
- `APP_NOTIFY_CRON`: the frequency in second of the heartbeat announce to the engine, default is 30

#### Start the application

In the [model_serving](../../services/digit_recognition/model_serving) directory, start the service with the following commands.

Generate the virtual environment and install the dependencies.

```sh
# Generate the virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install the requirements
pip install --requirement requirements.txt
```

Start the application.

```sh
# Start the application
APP_HOST=0.0.0.0 APP_PORT=8383 APP_ENGINE=http://localhost:8080 APP_SERVICE=http://localhost:8383 python3 main.py
```

Access the `digit_recognition` documentation on <http://localhost:8383/docs>.

Access the Engine documentation on <http://localhost:8080/docs> to validate the backend has been successfully registered to the Engine.

#### Run the tests

In the [model_serving](../../services/digit_recognition/model_serving) directory, run the tests with the following commands.

Install the additional packages.

```sh
# Install required packages for testing
pip3 install pytest pytest-asyncio aiofile
```

Run the tests.

```sh
# Run the tests
python3 -m pytest --asyncio-mode=auto
```

#### Run locally using Kubernetes (with minikube) and official Docker images

Start the service with the following commands. This will start the service with the official Docker images that are hosted on GitHub.

In the [model_serving](../../services/digit_recognition/model_serving) directory, start the service with the following commands.

```sh
# Start the digit_recognition backend
kubectl apply \
    -f kubernetes/digit-recognition.config-map.yml \
    -f kubernetes/digit-recognition.stateful.yml \
    -f kubernetes/digit-recognition.service.yml
```

Create a tunnel to access the Kubernetes cluster from the local machine. The terminal in which the tunnel is created must stay open.

```sh
# Open a tunnel to the Kubernetes cluster
minikube tunnel --bind-address 127.0.0.1
```

Access the `digit_recognition` documentation on <http://localhost:8383/docs>.

Access the Engine documentation on <http://localhost:8080/docs> to validate the backend has been successfully registered to the Engine.

#### Run locally using Kubernetes (with minikube) and a local Docker image

**Note**: The service StatefulSet (`digit-recognition.stateful.yml` file) must be deleted and recreated every time a new Docker image is created.

Start the service with the following commands. This will start the service with the a local Docker image for the service.

In the [model_serving](../../services/digit_recognition/model_serving) directory, build the Docker image with the following commands.

```sh
# Access the Minikube's Docker environment
eval $(minikube docker-env)

# Build the Docker image
docker build -t ghcr.io/csia-pme/csia-pme-digit-recognition:latest .

# Exit the Minikube's Docker environment
eval $(minikube docker-env -u)

# Edit the `kubernetes/digit-recognition.stateful.yml` file to use the local image by uncommented the line `imagePullPolicy`
#
# From
#
#        # imagePullPolicy: Never
#
# To
#
#        imagePullPolicy: Never
```

In the [model_serving](../../services/digit_recognition/model_serving) directory, start the service with the following commands.

```sh
# Start the digit_recognition backend
kubectl apply \
    -f kubernetes/digit-recognition.config-map.yml \
    -f kubernetes/digit-recognition.stateful.yml \
    -f kubernetes/digit-recognition.service.yml
```

Create a tunnel to access the Kubernetes cluster from the local machine. The terminal in which the tunnel is created must stay open.

```sh
# Open a tunnel to the Kubernetes cluster
minikube tunnel --bind-address 127.0.0.1
```

Access the `digit_recognition` documentation on <http://localhost:8383/docs>.

Access the Engine documentation on <http://localhost:8080/docs> to validate the backend has been successfully registered to the Engine.
