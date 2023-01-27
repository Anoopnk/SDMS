import time
import warnings
from datetime import timedelta, datetime

from astropy.units import Quantity

from .Helper import nowUTC
import astropy.units as u
import numpy as np
from gwpy.timeseries import TimeSeries


class BaseData(dict):
    """
    Base class for all data objects.
    """
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class BaseDataSet(BaseData):
    """
    Base class for dataset which can undergo basics analysis operations.
    """


class LaserMetaData(BaseData):
    """
    LaserMetaData class contains the metadata of the laser data.
    """
    SamplingRates = {
        0: 2.55 * u.us,
        1: 5 * u.us,
        2: 10 * u.us,
        3: 20 * u.us,
        4: 50 * u.us,
        5: 100 * u.us,
        6: 200 * u.us,
        7: 500 * u.us,
        8: 1000 * u.us
    }

    OUT = "01"

    Storage = {
        "Initialize": "AQ",
        "Start": "AS",
        "Status": "AN",
        "Stop": "AP",
        "Fetch": f"AO,{OUT}",
    }

    RawConfig = {
        "Tolerance": f"SW,LM,{OUT},",
        "SetStorage": f"SW,OK,{OUT},",
        "SurfaceToBeMeasured": f"SW,OA,T,{OUT},",
        "Scaling": f"SW,OB,{OUT},",
        "Filter": f"SW,OC,{OUT},0,",
        "MeasurementModeSensor": f"SW,OD,{OUT},",
        "MeasurementModeTarget": f"SW,HB,{OUT},",
        "TriggerMode": f"SW,OE,M,{OUT},",
        "Offset": f"SW,OF,{OUT},",
        "MeasurementType": f"SW,OI,{OUT},",
        "SamplingCycle": "SW,CA,",
        "DataStorage": "SW,CF,",
    }
    Programs = (
        ("+500.000, -500.000, 0000.000", "1", "0", "+000.000, +000.000, +999.999, +999.999", "0", "0", "0", "4", "+000.000", "0", "8", "0060000,1"),
    )
    CurrentProgram = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.Tolerance = "undefined"
        self.SetStorage = "undefined"
        self.SurfaceToBeMeasured = "undefined"
        self.Scaling = "undefined"
        self.Filter = "undefined"
        self.MeasurementModeSensor = "undefined"
        self.MeasurementModeTarget = "undefined"
        self.TriggerMode = "undefined"
        self.Offset = "undefined"
        self.MeasurementType = "undefined"
        self.SamplingCycle = "undefined"
        self.DataStorage = "undefined"

        self.update(self.CurrentConfig)

    @property
    def Frequency(self) -> int:
        return int(1 / self.dt.value)

    @property
    def WaitingTime(self) -> int:
        return int(self.dt.value * self.StorageSize)

    @property
    def StorageSize(self) -> int:
        return int(self.DataStorage.split(",")[-2])

    @property
    def dt(self) -> Quantity:
        return self.SamplingRates[int(self.SamplingCycle.split(",")[-1])].to(u.s)

    @property
    def CurrentConfig(self):
        prog = self.Programs[self.CurrentProgram]
        current_config = {}
        for (key, prefix), value in zip(self.RawConfig.items(), prog):
            current_config[key] = prefix + value
        return current_config

    def program_index(self, key: str):
        return list(self.RawConfig.keys()).index(key)

    def change_program(self, program: int):
        if program >= len(self.Programs):
            raise ValueError("Program {} does not exist".format(program))
        self.CurrentProgram = program
        self.update(self.CurrentConfig)


class LaserData(BaseDataSet):
    """
    LaserData is a dictionary that contains the data from the laser.
    Data is stored in a fixed format which is used by the DataHandler to save and load.
    """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.Data: list = []
        self.MetaData: LaserMetaData = LaserMetaData()
        self.StartTime: datetime = nowUTC()
        self.EndTime: datetime = nowUTC()

    @property
    def data_length(self):
        return len(self.Data)

    @property
    def has_nan(self):
        return np.isnan(self.Data).any()

    def insert(self, data: list):
        self.Data.extend(data)
        self.EndTime = nowUTC()
        self.StartTime = self.EndTime - timedelta(seconds=self.data_length * self.MetaData.dt.value)

    def parse_insert(self, data: str):
        """
        Parses the data from the laser serial and inserts it into the data object.
        """
        try:
            data = list(map(float, data.replace("FFFFFFF", "nan").strip().split(",")[1:]))
            self.insert(data)
        except ValueError:
            warnings.warn("Invalid data received from laser: {} ... {}".format(data[:10], data[-10:]))

    def timeseries(self):
        if self.has_nan:
            warnings.warn("Warning: Data contains NaN values. These will be replaced with 0.")
            data = np.nan_to_num(self.Data)
        else:
            data = self.Data
        return TimeSeries(data, unit=u.um, t0=self.StartTime.timestamp(),
                          dt=self.MetaData.dt, name="LVDT Laser")

        