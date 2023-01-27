from pathlib import Path
from .Helper import nowUTC


class FileManager:
    """
    This class takes care of the file management with the protocol in mind.
    Each data is per hour and is stored in an organized manner with the structure in year, month and day.
    Each day folder may contain more than one dataset relating to different source and/or experiment.
    """

    tags = {
        "test": "test",
        "experiment": "experiment",
        "calibration": "calibration",
        "temp": "temp"
    }

    def __init__(self, root_path: Path = Path("/data/data/")):
        self.root_path = root_path
        self.current_date = None
        self.current_path = "temp"
        self.current_full_path = self.root_path / "temp"

        if not self.root_path.exists():
            self.root_path.mkdir(parents=True)

    def filepath(self, tag: str = "test") -> Path:
        """
        Get the appropriate filepath for the current date including the tag.
        :param tag: Tag for the current measurement. Default is "test".
        :return: Path object of the location.
        """
        current_date = nowUTC().date()
        tag = tag.strip().lower()

        # File path based on date
        if current_date != self.current_date:
            self.current_date = current_date
            self.current_path = "{:04d}/{:02d}/{:02d}".format(self.current_date.year, self.current_date.month, self.current_date.day)

        # Extended file path based on tag
        if tag in self.tags:
            self.current_path = "{}/{}".format(self.tags[tag], self.current_path)
        else:
            self.current_path = "{}/{}".format(self.tags["test"], self.current_path)

        # Create full path
        self.current_full_path = self.root_path / self.current_path
        self.current_full_path.mkdir(parents=True, exist_ok=True)

        return self.current_full_path


class FileHandler:
    """
    This class handles the file opening and closing correctly.
    """
    filemanager = FileManager()

    def __init__(self, filename: str = None, tag: str = "test"):
        self.tag = tag
        filename = filename.strip().lower() if filename else "data"
        self.filename = nowUTC().strftime("%Y%m%d_{}".format(filename))
        self._file = self.filemanager.filepath(self.tag) / self.filename

    def open_hdf5store(self, mode: str = "a"):
        """
        Open a HDF5Store file.
        :param mode: Mode to open the file. Default is "a" for append.
        :return: HDF5Store object.
        """
        return pd.HDFStore(self._file, mode=mode)


class File:

    @property
    def file(self):
        return self._file