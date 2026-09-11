# TensorFlow Serving

## Serve a Tensorflow model in 60 seconds

```bash
# Download the TensorFlow Serving Docker image and repo
docker pull tensorflow/serving

# Start TensorFlow Serving container and open the REST API port
docker run -t --rm -p 8501:8501 \
    -v "$TESTDATA/saved_model_half_plus_two_cpu:/models/half_plus_two" \
    -e MODEL_NAME=half_plus_two \
    tensorflow/serving &
```

## Python API

```bash
pip install tensorflow-serving-api
```
