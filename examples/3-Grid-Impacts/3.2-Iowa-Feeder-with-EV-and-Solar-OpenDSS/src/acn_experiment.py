import pytz
from datetime import datetime, timezone
import numpy as np
import cvxpy as cp
import os
from acnportal import acnsim
from acnportal.signals.tariffs import TimeOfUseTariff
from acnportal import algorithms
from adacharge import (
    ObjectiveComponent,
    total_energy,
    tou_energy_cost,
    quick_charge,
    equal_share,
    AdaptiveSchedulingAlgorithm,
    demand_charge,
    aggregate_power,
)


API_KEY = "DEMO_TOKEN"


def iso_format_basic(dt):
    """ Return time in ISO-8601 basic format."""
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S")


class ACNExperiment:
    """Class container for ACN-Sim experiment.

    Args:
        site (str): Name of the site to get data from.
        start (datetime): Time to start the simulation.
        end (datetime): Time to end the simulation.
        period (int): Length of each interval of the simulation. [min]
        voltage (int): Assumed voltage used when charging. [V]
        default_battery_power (float): Assumed maximum battery power for each EV. [kW]
        alg_name (str): Name of the algorithm to use.
        tariff_name (str): Name of the tariff to use.

    Returns:
        acnsim.EventQueue: Queue of events to drive the simulation.
    """

    def __init__(
        self,
        site: str,
        start: datetime,
        end: datetime,
        alg_name: str,
        tariff_name: str,
        external_load: np.ndarray = None,
        external_load_name: str = "",
        bus_transformer_cap=225,
        events_dir="events",
        sim_dir="sims",
        sim_timezone="America/Los_Angeles"
    ):
        self.timezone = pytz.timezone(sim_timezone)
        self.start = self.timezone.localize(start)
        self.end = self.timezone.localize(end)
        self.site = site
        self.period = 5
        self.voltage = 208
        self.default_battery_power = 6.656
        self.alg_name = alg_name
        self.tariff_name = tariff_name
        self.external_load = external_load
        self.external_load_name = external_load_name
        self.bus_transformer_capacity = bus_transformer_cap
        self.sim = None
        self.events_dir = events_dir
        self.sim_dir = sim_dir

    def events_filename(self):
        """ Filename under which to store the the events queue."""
        filename = (
            f"site-{self.site}_start-{iso_format_basic(self.start)}"
            f"_end-{iso_format_basic(self.end)}.json"
        )
        return os.path.join(self.events_dir, filename)

    def sim_filename(self):
        """ Filename under which to store the ACN-Sim simulation. """
        filename = (
            f"site-{self.site}_start-{iso_format_basic(self.start)}"
            f"_end-{iso_format_basic(self.end)}"
            f"_alg_name-{self.alg_name}_tariff_name-{self.tariff_name}"
            f"_external_load_name-{self.external_load_name}.json"
        )
        return os.path.join(self.sim_dir, filename)

    def get_events(self):
        """Get events via the ACN-Data API.

        Returns:
            acnsim.EventQueue: Queue of events to drive the simulation.
        """
        filename = self.events_filename()
        if os.path.exists(filename):
            return acnsim.EventQueue.from_json(filename)
        else:
            events = acnsim.acndata_events.generate_events(
                API_KEY,
                self.site,
                self.start,
                self.end,
                self.period,
                self.voltage,
                self.default_battery_power,
            )
            if not os.path.exists(self.events_dir):
                os.makedirs(self.events_dir)
            events.to_json(filename)
            return events

    def get_charging_network(self):
        """Get charging network by name.

        Args:
            site (str): Name of the site to get data from.
            voltage (int): Voltage of the EVSEs. [V]

        Returns:
            ChargingNetwork
        """
        if self.site == "caltech":
            return acnsim.sites.caltech_acn(basic_evse=True, voltage=self.voltage)
        elif self.site == "jpl":
            return acnsim.sites.jpl_acn(basic_evse=True, voltage=self.voltage)

    def get_scheduling_algorithm(self):
        """Get scheduling algorithm.

        Args:
            alg_name (str): Name of the scheduling algorithm.

        Returns:
            acnsim.BaseAlgorithm-like
        """

        def days_remaining_scale_demand_charge(
            rates,
            infrastructure,
            interface,
            baseline_peak=0,
            days_in_month=30,
            **kwargs,
        ):
            day_index = interface.current_time // ((60 / interface.period) * 24)
            day_index = min(day_index, days_in_month - 1)
            scale = 1 / (days_in_month - day_index)
            dc = demand_charge(
                rates, infrastructure, interface, baseline_peak, **kwargs
            )
            return scale * dc

        def load_flattening(
            rates,
            infrastructure,
            interface,
            external_signal=None,
            scaling_factor=1,
            **kwargs,
        ):
            t = interface.current_time
            horizon = rates.shape[1]
            aggregate_rates_kW = aggregate_power(rates, infrastructure)
            if external_signal is None:
                total_aggregate = aggregate_rates_kW
            else:
                total_aggregate = aggregate_rates_kW + external_signal[t : t + horizon]
            return -cp.sum_squares(total_aggregate / scaling_factor)

        if self.alg_name == "unctrl":
            return algorithms.UncontrolledCharging()
        elif self.alg_name == "llf":
            return algorithms.SortedSchedulingAlgo(algorithms.least_laxity_first)
        elif self.alg_name == "min_cost":
            revenue = 0.3
            objective = [
                ObjectiveComponent(total_energy, revenue),
                ObjectiveComponent(tou_energy_cost),
                ObjectiveComponent(days_remaining_scale_demand_charge),
                ObjectiveComponent(quick_charge, 1e-4),
                ObjectiveComponent(equal_share, 1e-9),
            ]
            return AdaptiveSchedulingAlgorithm(
                objective, solver="MOSEK", max_recompute=1
            )
        elif "load_flattening" in self.alg_name:
            peak_limit = (
                (self.bus_transformer_capacity - self.external_load) * 1000 / 208
            )
            objective = [
                ObjectiveComponent(total_energy, 100),
                ObjectiveComponent(
                    load_flattening,
                    1,
                    {"external_signal": self.external_load, "scaling_factor": 100},
                ),
                ObjectiveComponent(quick_charge, 1e-3),
            ]
            if "ECOS" in self.alg_name:
                return AdaptiveSchedulingAlgorithm(
                    objective, solver="ECOS", max_recompute=1, peak_limit=peak_limit
                )
            else:
                return AdaptiveSchedulingAlgorithm(
                    objective, solver="MOSEK", max_recompute=1, peak_limit=peak_limit
                )

    def build(self):
        """ Build experiment from configuration. """
        events = self.get_events()
        network = self.get_charging_network()
        sch = self.get_scheduling_algorithm()
        signals = {"tariff": TimeOfUseTariff(self.tariff_name)}
        return acnsim.Simulator(
            network, sch, events, self.start, period=self.period, signals=signals
        )

    def run(self):
        """ Run internal simulation. """
        filename = self.sim_filename()
        if os.path.exists(filename):
            self.sim = acnsim.Simulator.from_json(filename)
        else:
            self.sim = self.build()
            self.sim.run()
            if not os.path.exists(self.sim_dir):
                os.makedirs(self.sim_dir)
            self.sim.to_json(filename)


if __name__ == "__main__":
    tz = pytz.timezone("America/Los_Angeles")
    start_time = tz.localize(datetime(2019, 7, 1))
    end_time = tz.localize(datetime(2019, 8, 1))
    sites = ["jpl", "caltech"]
    algs = ["unctrl", "min_cost", "llf"]
    tariffs = [
        "sce_tou_ev_4_march_2019",
        "sce_tou_ev_8_june_2019",
        "pge_a10_tou_aug_2019",
    ]
    for site in sites:
        for alg in algs:
            for tariff in tariffs:
                config = {
                    "site": site,
                    "start": start_time,
                    "end": end_time,
                    "alg_name": alg,
                    "tariff_name": tariff if alg != "min_cost" else tariffs[0],
                }
                print(config)
                ex = ACNExperiment(**config)
                ex.run()
