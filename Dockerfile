# Start from a core stack version
FROM jupyter/scipy-notebook:latest

# Install acnportal with specific branch
RUN pip install git+https://github.com/zach401/acnportal
RUN pip install git+https://github.com/zach401/adacharge