# ---------- build stage ----------
FROM public.ecr.aws/lambda/python:3.11 AS build

# System deps for librosa + ffmpeg
RUN yum install -y gcc gcc-c++ make cmake git \
    && yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
    && yum install -y ffmpeg fftw-devel libsndfile libsndfile-devel \
    && pip install --upgrade pip wheel

WORKDIR /opt
COPY requirements_production.txt .

# Build wheels so we don't compile in the runtime layer
RUN pip wheel -r requirements_production.txt -w /wheels

# ---------- runtime stage ----------
FROM public.ecr.aws/lambda/python:3.11

# 1. Copy Python deps
COPY --from=build /wheels /opt/python

# 2. Copy ffmpeg binary and required libraries
COPY --from=build /usr/bin/ffmpeg /usr/bin/ffmpeg
COPY --from=build /usr/lib64/libavcodec.so* /usr/lib64/
COPY --from=build /usr/lib64/libavformat.so* /usr/lib64/
COPY --from=build /usr/lib64/libavutil.so* /usr/lib64/
COPY --from=build /usr/lib64/libswresample.so* /usr/lib64/
COPY --from=build /usr/lib64/libswscale.so* /usr/lib64/
COPY --from=build /usr/lib64/libsndfile.so* /usr/lib64/
COPY --from=build /usr/lib64/libFLAC.so* /usr/lib64/
COPY --from=build /usr/lib64/libogg.so* /usr/lib64/
COPY --from=build /usr/lib64/libvorbis.so* /usr/lib64/
COPY --from=build /usr/lib64/libvorbisenc.so* /usr/lib64/

# 3. Install Python packages from wheels
RUN pip install --no-index --find-links /opt/python \
    pydub librosa soundfile numpy scipy boto3 requests

# 4. Add source
COPY professional_mixer_production.py ${LAMBDA_TASK_ROOT}/
COPY audio_processor.py ${LAMBDA_TASK_ROOT}/
COPY s3_manager.py ${LAMBDA_TASK_ROOT}/
COPY performance_optimizer.py ${LAMBDA_TASK_ROOT}/

# 5. Set environment variable for PyDub
ENV FFMPEG_BINARY=/usr/bin/ffmpeg

# 6. Bootstrap
CMD ["professional_mixer_production.lambda_handler"]