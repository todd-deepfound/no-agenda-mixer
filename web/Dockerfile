# ---------- build stage ----------
FROM public.ecr.aws/lambda/python:3.11 AS build

# System deps for Python compilation
RUN yum install -y gcc gcc-c++ make cmake git python3-devel && \
    pip install --upgrade pip wheel

WORKDIR /opt
COPY requirements_production.txt .

# Build wheels so we don't compile in the runtime layer
RUN pip wheel -r requirements_production.txt -w /wheels

# ---------- runtime stage ----------
FROM public.ecr.aws/lambda/python:3.11

# Install ffmpeg from static build (works on any Linux)
RUN yum install -y tar xz && \
    cd /tmp && \
    curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o ffmpeg.tar.xz && \
    tar xf ffmpeg.tar.xz && \
    cp ffmpeg-*/ffmpeg /usr/local/bin/ && \
    chmod +x /usr/local/bin/ffmpeg && \
    rm -rf /tmp/ffmpeg*

# Copy Python deps
COPY --from=build /wheels /opt/python

# Install Python packages from wheels
RUN pip install --no-index --find-links /opt/python \
    pydub librosa soundfile numpy scipy boto3 requests

# Add source
COPY professional_mixer_production.py ${LAMBDA_TASK_ROOT}/
COPY audio_processor.py ${LAMBDA_TASK_ROOT}/
COPY s3_manager.py ${LAMBDA_TASK_ROOT}/
COPY performance_optimizer.py ${LAMBDA_TASK_ROOT}/

# Set environment variable for PyDub
ENV FFMPEG_BINARY=/usr/local/bin/ffmpeg

# Bootstrap
CMD ["professional_mixer_production.lambda_handler"]