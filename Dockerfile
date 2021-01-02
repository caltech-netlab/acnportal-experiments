# Start from a core stack version
FROM jupyter/scipy-notebook:latest

# Install acnportal with specific branch
RUN pip install git+https://github.com/zach401/acnportal@EHN_stochastic_network
RUN pip install git+https://github.com/zach401/adacharge
