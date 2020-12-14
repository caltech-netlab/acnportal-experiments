# ACN Research Portal Examples
The purpose of this repository is to share examples of how the [ACN Research Portal
(acnportal)](https://github.com/zach401/acnportal) can be used to answer research
 questions.

## Getting Started
There are several ways to get started using these examples. 

#### Colab
The easiest way to get started running these example is to run them in your browser
 using Google's Colab service. With this service you have access to a fully managed
 environment without needing to install anything on your local machine. 

Links to Colab for each example can be found in the **Examples** section below. 

When using these examples in Colab, you will likely see the message "Warning: This
 notebook was not authored by Google." 
 Click "Run Anyway". If you feel more comfortable, you can reset your runtimes 
 if other Colab notebooks have access to your private data. 
 **This script does not attempt to access any of your data.**


#### Docker 
While Colab is a great tool for sharing experiments, some experiments are 
 long-running and benefit from running locally. To make running these experiments
 easier, you can use the docker image to run all these examples with Jupyter Lab
 within a docker container. 
 
To run with docker:
 
First clone the repository to your local machine:
 ```
git clone https://github.com/caltech-netlab/acnportal-experiments
```

Navigate to the cloned folder and run
```
./run.sh
```

You can then click the link in your terminal to open Jupyter lab. All examples can
 then be run within the container. Since we mount the code directories, any changes you
 make within the container will be reflected on your local file system. 

#### Running Locally
If you prefer to run locally without docker, we recommend using venv or your favorite 
 virtual environment tool (e.g. conda). 
 
First clone the repository to your local machine:
```
git clone https://github.com/caltech-netlab/acnportal-experiments
```

Navigate to the cloned folder, then install the dependencies using 
#### TODO: Add requirements.txt.
```
pip install -r requirements.txt
```  

You can then spin up a Jupyter Lab instance using
```
jupyter lab
```

You can then click the link in your terminal to open Jupyter lab. 

## Examples
**The repository is divided into several sections (directories):**
### 1. Infrastructure Evaluation
#### 1.1 Unbalanced Three-Phase Systems
*How does phase imbalance affect the efficiency and safety of a large-scale
  charging system?*

Currently, most charging algorithms in the literature rely on constraints which assume 
single-phase or balanced three-phase operation. In this experiment, we demonstrate why 
these assumptions are insufficient for practical charging systems. 
#### TODO: Which MPC alg?
For this experiment we use the LLF and MPC algorithms. We consider two cases for each 
algorithm. In the first, the algorithms consider a simplified single-phase 
representation of the constraints in  the network. In the second, the algorithms use
the full three-phase system model. In both cases, we evaluate the algorithms using the
true three-phase network model.
#### TODO: Change these links to reflect new repo name.
[Colab Link](https://colab.research.google.com/github/zach401/ACN-Sim-Demo/blob/master/examples/1-Infrastructure-Evaluation/1.1-Unbalanced-Three-Phase-Systems/1.1-unbalanced-three-phase-systems.ipynb)
  
#### 1.2 Comparing Infrastructure Designs
*How can we use acnportal to evaluate the tradeoffs between level-1 and level-2 and
 managed vs unmanaged charging?*

In this case study, we demonstrate how ACN-Data and ACN-Sim can be used to evaluate 
infrastructure configurations and algorithms. We consider the case of a site host who 
expects to charge approximately 100 EVs per day with a demand pattern similar to that 
of JPL.

The site host has several options, including  
*   102 Uncontrolled Level-1 EVSEs with a 200 kW Transformer
*   30 Uncontrolled Level-2 EVSEs with a 200 kW Transformer
*   102 Uncontrolled Level-2 EVSEs with a 670 kW Transformer
*   102 Smart Level-2 EVSEs running LLF with a 200 kW Transformer

We evaluate the scenarios based on the number of times drivers would have to swap
parking places to allow other drivers to charge, the percentage of total demand met, 
and the operating costs (calculated using ACN-Sim's integration with utility tariffs). 
This case study demonstrates the significant benefits of developing smart EV charging
systems in terms of reducing both capital costs (transformer capacity) and operating
costs.

[Colab Link](https://colab.research.google.com/github/zach401/ACN-Sim-Demo/blob/master/examples/1-Infrastructure-Evaluation/1.2-Comparing-Infrastructure-Designs/1.2-comparing-infrastructure-designs.ipynb)


### 2. Algorithm Comparison
#### 2.1 Comparing Algorithms with Constrained Infrastructure
*How can we compare different scheduling algorithms?*
#### TODO: Add MPC QC, CM to algorithm list, here and in notebook
In this experiment we compare the performance of the Round Robin, 
First-Come First-Served, Earliest Deadline First, and 
Least Laxity First algorithms. To understand how these algorithms 
cope with constrained infrastructure, we limit the capacity of the transformer
feeding the charging network. We then compare what percentage of energy demands each
algorithm is able to meet. We also consider the current unbalance caused by each 
algorithm to help understand why certain algorithms are able to deliver more or less 
energy at a given infrastructure capacity.

[Colab Link](https://colab.research.google.com/github/zach401/ACN-Sim-Demo/blob/master/examples/examples/2-Algorithm-Comparison/2.1-Comparing-Algorithms-with-Constrained-Infrastructure/2.1-comparing-algorithms-with-constrained-infrastructure.ipynb)


### 3. Grid Impacts
#### 3.1 Simple Feeder with EV and Solar (PandaPower)
*What effects will large-scale charging systems have on the distribution system?*

In this experiment, we use ACN-Sim in conjunction with pandapower to understand the 
effects of EV charging on the electrical grid. Specifically, we use outputs from 
simulations of the JPL ACN with different charging algorithms as inputs to a pandapower 
power flow at varying timesteps in a simple electrical grid. We experiment with adding 
EV charging to a grid already loaded with offices.

In a general sense, this tutorial demonstrates how ACN-Sim can be used to evaluate 
scheduled charging algorithms in the context of grid-level effects by feeding results 
from ACN-Sim Simulations into pandapower power flows.

[Colab Link](https://colab.research.google.com/github/zach401/ACN-Sim-Demo/blob/master/examples/3-Grid-Impacts/3.1-Simple-Feeder-with-EV-and-Solar-PandaPower/3.1-simple-feeder-with-ev-and-solar-pandapower.ipynb)

#### 3.2 Iowa Feeder with EV and Solar (OpenDSS)
*What effects will a large-scale charging system have on a real distribution system?*

In this experiment, we use ACN-Sim in conjunction with OpenDSS to understand the 
effects of EV charging on a distribution feeder in Iowa. As in 3.1, we use outputs
from simulations of the JPL ACN with different charging algorithms as inputs to a
OpenDSS power flow at varying timesteps. The distribution feeder includes smart meter
data at each load natively; we add EV charging on top of the base load at a single
high-capacity node. We show that while uncontrolled charging causes voltage issues in
the overall grid, load flattening mitigates these issues, and load flattening with
solar generation eliminates them entirely.

In a general sense, this tutorial demonstrates how ACN-Sim can be used to evaluate 
scheduled charging algorithms in the context of grid-level effects by feeding results 
from ACN-Sim Simulations into OpenDSS power flows.

[Colab Link](https://colab.research.google.com/github/zach401/ACN-Sim-Demo/blob/master/examples/3-Grid-Impacts/3.1-Simple-Feeder-with-EV-and-Solar-PandaPower/3.1-simple-feeder-with-ev-and-solar-pandapower.ipynb)


## Papers
The examples in this repository have been used as the basis for several academic
 papers. To ensure reproducibility, we have tagged the version of the repository used
 in each paper, allowing you to run the exact code used in those works. While ideally
 this code would not need to change over time, the ACN Research Portal is under
 constant development. To make these examples relevant over time, we may update
 them to use new interfaces or best practices as they are developed. 

### ACN-Sim: An Open-Source Simulator for Data-Driven Electric Vehicle Charging Research
*IEEE International Conference on Communications, Control, and Computing Technologies for Smart Grids (SmartGridComm),
Beijing, China, October 2019*

Z. Lee, D. Johansson, S. H. Low. 
[ACN-Sim: An Open-Source Simulator for Data-Driven Electric Vehicle Charging Research](https://ev.caltech.edu/assets/pub/ACN_Sim_Open_Source_Simulator.pdf), 
Proc. of the IEEE International Conference on Communications, Control, and Computing Technologies for Smart Grids (SmartGridComm),
Beijing, China, October 2019

Relevant Experiments:

[1.1 Unbalanced Three Phase Systems](#11-unbalanced-three-phase-systems)

[2.1 Comparing Algorithms with Constrained Infrastructure](#21-comparing-algorithms-with-constrained-infrastructure)
#### TODO: Add latest paper
