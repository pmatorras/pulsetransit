# Use a lightweight Python base image
FROM python:3.11-slim

# Hugging Face Spaces strongly recommends running as a non-root user (User ID 1000)
RUN useradd -m -u 1000 user
USER user

# Set environment variables for the user and Streamlit
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    STREAMLIT_SERVER_PORT=7860 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Set the working directory
WORKDIR $HOME/app

# Copy all project files into the container with the correct permissions
COPY --chown=user:user . $HOME/app

# Install your package using your existing pyproject.toml
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Expose the default Hugging Face Spaces port
EXPOSE 7860

# Run the Streamlit dashboard
CMD ["streamlit", "run", "src/pulsetransit/dashboard/app.py"]
