FROM python:3.9-slim
WORKDIR /app
RUN pip install flask gunicorn
COPY app.py .
RUN mkdir -p /data
VOLUME ["/data"]
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
