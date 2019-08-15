# ACN-Sim Case Study
## Comparing Baseline Algorithms in Constrained Infrastructure

To demonstrate the usefulness of ACN-Sim we present two simple case studies.

### unbalanced_three_phase_infrastructure.ipynb

In the first study, we demonstrate the importance of considering the three-phase nature of charging networks by showing that only considering limits on the aggregate charging current can lead to line overloads in an unbalanced three-phase system.

### baseline_algorithms_w_constrained_infrastructure.ipynb

In the second study, we compare the percentage of energy demands which are met at various infrastructure capacities for Earliest Deadline First, Least Laxity First, First Come First Served, and Round Robin. 

## Try it.
You can try these experiments online without needing to install anything on your local machine using Google Colab. 

### unbalanced_three_phase_infrastructure.ipynb
https://colab.research.google.com/github/zach401/acnsim_baseline_comparison/blob/master/unbalanced_three_phase_infrastructure.ipynb

### baseline_algorithms_w_constrained_infrastructure.ipynb
https://colab.research.google.com/github/zach401/acnsim_baseline_comparison/blob/master/baseline_algorithms_w_constrained_infrastructure.ipynb

*Note that the full experiment involves running many simulations, each 1 month long. Consider running this experiment locally or shortening the time horizon to avoid Colab timeouts.*

You will likely see a message "Warning: This notebook was not authored by Google." Click "Run Anyway". If you feel more comfortable, you can reset your runtimes, if other Colab notebooks have access to your private data. **This script does not attempt to access any of your data.**
