FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

# Run as any non-root user you like (compose `user:`); ports and cert paths are
# configured through the environment — see README.md.
CMD ["python", "-u", "main.py"]
