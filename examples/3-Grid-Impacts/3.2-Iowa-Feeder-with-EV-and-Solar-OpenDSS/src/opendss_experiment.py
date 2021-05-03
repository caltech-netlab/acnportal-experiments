from datetime import timedelta
import opendssdirect as dss
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from collections import defaultdict
from tqdm import tqdm
import os
import tempfile

# TODO: Generalize (maybe as inputs to Constructor?).
CIRCUIT_DIR = "iowa_dist_feeder"
LOAD_DIR = "iowa_data"


def export_to_df(measurement: str):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, f"{measurement}.csv")
        saved_file = dss.run_command(f"export {measurement} {path}")
        return pd.read_csv(saved_file, index_col=0)


class OpenDSSExperiment:
    """ Simple class to contain a single experiment. """

    def __init__(self, start, horizon, period, reg_control=True):
        self.start = start
        self.horizon = horizon  # minutes
        self.period = period  # minutes
        self.end = self.start + timedelta(minutes=horizon)
        self.reg_control = reg_control
        self.P, self.Q = self.get_load_data()

        self.build_circuit()

        # Information Storage Variables
        self.voltage_pu = pd.DataFrame(index=dss.Circuit.AllNodeNames())
        self._taps_dict = defaultdict(dict)
        self._wdg_dict = defaultdict(dict)

        self._summary_dict = dict()
        self._overload_dict = dict()
        self._capacity_dict = dict()
        self._currents_dict = dict()
        self._profile_dict = dict()

    @property
    def wdg(self):
        return pd.DataFrame(self._wdg_dict)

    @property
    def taps(self):
        return pd.DataFrame(self._taps_dict)

    def get_load_data(self):
        """ Get baseline load data from csv files. """
        loads = {}
        for pq in "PQ":
            loads[pq] = pd.read_csv(
                f"{LOAD_DIR}/iowa_nodal_{pq}.csv", parse_dates=True, index_col=0
            )
            loads[pq] = loads[pq][self.start : self.end + timedelta(hours=1)]
            loads[pq] = loads[pq].resample(f"{self.period}T").bfill()
        return loads["P"], loads["Q"]

    def build_circuit(self):
        """ Set up the Iowa test circuit in OpenDSS. """
        dss.run_command("Clear")

        # Initiate a new circuit called "240_node_test_system"
        dss.run_command("new circuit.240_node_test_system")

        dss.run_command(f"Redirect {CIRCUIT_DIR}/Vsource.dss")
        dss.run_command(f"Redirect {CIRCUIT_DIR}/SubTransformer.dss")
        if self.reg_control:
            dss.run_command(f"Redirect {CIRCUIT_DIR}/RegControl.dss")
        dss.run_command(f"Redirect {CIRCUIT_DIR}/DistriTransformer.dss")
        dss.run_command(f"Redirect {CIRCUIT_DIR}/Linecode.dss")
        dss.run_command(f"Redirect {CIRCUIT_DIR}/Line.dss")
        dss.run_command(f"Redirect {CIRCUIT_DIR}/CircuitBreaker.dss")
        dss.run_command(f"Redirect {CIRCUIT_DIR}/Load.dss")
        dss.run_command(f"Redirect {CIRCUIT_DIR}/Capacitor.dss")
        dss.run_command("New EnergyMeter.FeederB Line.L_2001_2002 1")
        # dss.run_command("New EnergyMeter.Total Element=Transformer.Sub_Xfmr Terminal=1")

        # Set base voltage as 69 kV, 13.8 kV, 0.208 kV
        dss.run_command('Set VoltageBases = "69.0, 13.8, 0.208"')
        dss.run_command("CalcVoltageBases")

    def add_load(self, acn_buses, ev_load, ev_load_offset=0):
        """ Add additional load to the baseline load. If negative, this can serve as generation. """
        for acn_bus in acn_buses:
            load = ev_load[
                ev_load_offset : ev_load_offset + self.horizon // self.period
            ]
            if acn_bus not in self.P:
                self.P[acn_bus] = np.zeros(self.P.shape[0])
            bus_index = self.P.columns.get_loc(acn_bus)
            self.P.iloc[: self.horizon // self.period, bus_index] += np.real(load)

            if acn_bus not in self.Q:
                self.Q[acn_bus] = np.zeros(self.Q.shape[0])
            bus_index = self.Q.columns.get_loc(acn_bus)
            self.Q.iloc[: self.horizon // self.period, bus_index] += np.imag(load)

    def step_loads(self, t):
        """ Update loads within the OpenDSS model using the dataframes P and Q. """
        for load_name in dss.utils.Iterator(dss.Loads, "Name"):
            name = load_name()
            if name in self.P:
                dss.Loads.kW(dss.Loads.kW() + self.P[name][t])
            else:
                dss.Loads.kW(0)

            if name in self.Q:
                dss.Loads.kvar(dss.Loads.kvar() + self.Q[name][t])
            else:
                dss.Loads.kvar(0)

    def store_voltages(self, time):
        """ Store per unit voltage for each node. """
        names = []
        volts = []
        for name in dss.Circuit.AllBusNames():
            # Set the Active bus
            dss.Circuit.SetActiveBus(name)
            # Compute the voltage
            voltages = [
                abs(complex(i[0], i[1])) for i in zip(*[iter(dss.Bus.PuVoltage())] * 2)
            ]
            for i, node in enumerate(dss.Bus.Nodes()):
                names.append(f"{name}.{node}")
                volts.append(voltages[i])
        self.voltage_pu[time] = pd.Series(volts, names)

    def store_transformer_info(self, time):
        """ Store winding and tap position for transformer. """
        for name in dss.utils.Iterator(dss.Transformers, "Name"):
            if name() in set(f"sub_regulator_{p}" for p in "abc"):
                self._taps_dict[time][name()] = dss.Transformers.Tap()
                self._wdg_dict[time][name()] = dss.Transformers.Wdg()

    def run(self, detailed_metrics=True):
        """ Run the experiment. """
        steps = self.horizon // self.period
        for t in tqdm(range(steps)):
            self.build_circuit()
            self.step_loads(t)
            dss.run_command("Solve")
            time = self.P.index[t]
            self.store_voltages(time)
            self.store_transformer_info(time)
            if detailed_metrics:
                self._summary_dict[time] = export_to_df("summary")
                self._overload_dict[time] = export_to_df("overload")
                self._capacity_dict[time] = export_to_df("capacity")
                self._currents_dict[time] = export_to_df("currents")
                self._profile_dict[time] = export_to_df("profile")

    def plot_voltage(self, ax=None, legend=False, title=None):
        """ Plot maximum and minimum voltage in the network. """
        df = self.voltage_pu
        df.max(axis=0).plot(ax=ax, label="Max voltage")
        df.min(axis=0).plot(ax=ax, label="Min voltage")
        if ax is None:
            ax = plt
        ax.axhline(1.05, linestyle="--", color="grey")
        ax.axhline(0.95, linestyle="--", color="grey")
        ax.set_xlabel("Time of day")
        ax.set_ylabel("Voltage p.u.")
        if title is not None:
            ax.set_title(title)
        if legend:
            ax.legend(loc="best")
