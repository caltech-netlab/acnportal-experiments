# coding=utf-8
"""
Objects and wrappers to run an ACN-Sim + OpenDSS co-simulation.
"""
from typing import Optional, Dict

import numpy as np
from acnportal import acnsim

# noinspection PyUnresolvedReferences
from acn_experiment import ACNExperiment

# noinspection PyUnresolvedReferences
from opendss_experiment import OpenDSSExperiment


class ACNOpenDSSCompositeExperiment:
    """Class container for ACN-Sim + OpenDSS co-simulation.

    Attributes:
        open_dss_experiment (OpenDSSExperiment): Configuration of OpenDSS Experiment.
        acn_experiments (Optional[Dict[str, ACNExperiment]]): Configuration of ACN Experiment.

    """

    acn_experiments: Optional[Dict[str, ACNExperiment]]

    def __init__(
        self,
        open_dss_configs,
        acn_configs: Optional[Dict[str, Dict]] = None,
        unbalanced: bool = True,
        ev_load_offset: float = 0,
    ):
        """
        The ACNExperiment is optional here. If None is provided as the configs, the
        ACNExperiment is set to None and the OpenDSS experiment is run without any
        extra loads.

        TODO: Support multiple configs for multiple acn experiments at different loads.
        """
        self.acn_experiments = (
            {
                acn_bus: ACNExperiment(**acn_config)
                for acn_bus, acn_config in acn_configs.items()
            }
            if acn_configs is not None
            else None
        )
        self.open_dss_experiment = OpenDSSExperiment(**open_dss_configs)
        if acn_configs is not None:
            self.acn_buses = acn_configs.keys()
        else:
            self.acn_buses = []
        self.unbalanced = unbalanced
        self.ev_load_offset = ev_load_offset

    def add_acn_load(self, acn_bus):
        acn_experiment = self.acn_experiments[acn_bus]
        if self.unbalanced:
            ev_load = acnsim.constraint_currents(
                acn_experiment.sim, return_magnitudes=True
            )
            if acn_experiment.site == "jpl":
                for phase in "ABC":
                    ev_load[f"Secondary {phase}"] = (
                        ev_load[f"Third/Fourth Floor Transformer Secondary {phase}"]
                        + ev_load[f"First Floor Transformer Secondary {phase}"]
                    )

            voltages = {
                "Secondary A": 120,
                "Secondary B": 120 * np.exp(1j * np.deg2rad(-120)),
                "Secondary C": 120 * np.exp(1j * np.deg2rad(120)),
            }
            for phase in voltages:
                ev_load[phase] = voltages[phase] * np.conj(ev_load[phase]) / 1000

            # horizon = ev_load["Secondary A"].shape[0]
            # baseline_load = (
            #     dss_ex.P[f"load_{acn_bus}"][:horizon]
            #     + 1j * dss_ex.Q[f"load_{acn_bus}"][:horizon]
            # ) / 3
            self.open_dss_experiment.add_load(
                [f"load_{acn_bus}_a"], ev_load["Secondary A"], self.ev_load_offset
            )
            self.open_dss_experiment.add_load(
                [f"load_{acn_bus}_b"], ev_load["Secondary B"], self.ev_load_offset
            )
            self.open_dss_experiment.add_load(
                [f"load_{acn_bus}_c"], ev_load["Secondary C"], self.ev_load_offset
            )
        else:
            self.open_dss_experiment.add_load(
                [f"load_{acn_bus}"],
                acnsim.aggregate_power(acn_experiment.sim),
                self.ev_load_offset,
            )

    def add_acn_loads(self):
        for acn_bus in self.acn_buses:
            self.add_acn_load(acn_bus)

    def add_general_load(
        self, load_bus: str, load: np.ndarray, load_offset: float = 0
    ) -> None:
        """Add a time-varying balanced load (or negative for generation) to the
        experiment."""
        self.open_dss_experiment.add_load(
            [f"load_{load_bus}"], load, load_offset,
        )

    def add_general_loads(
        self, load: np.ndarray, load_offset: float = 0, buses=None
    ) -> None:
        """Adds a to all acn buses."""
        if buses is None:
            for acn_bus in self.acn_buses:
                self.add_general_load(acn_bus, load, load_offset)
        else:
            for bus in buses:
                self.add_general_load(bus, load, load_offset)

    def run_dss(self, detailed_metrics=True):
        """ Run the OpenDSS experiment. """
        self.open_dss_experiment.run(detailed_metrics=detailed_metrics)

    def run_acn(self):
        """ Run the ACN-Sim experiments. """
        for acn_experiment in self.acn_experiments.values():
            acn_experiment.run()

    def plot_dss_voltages(self, ax=None, legend=False, title=None):
        """ Plot maximum and minimum voltage in the distribution feeder. """
        self.open_dss_experiment.plot_voltage(ax=ax, legend=legend, title=title)
