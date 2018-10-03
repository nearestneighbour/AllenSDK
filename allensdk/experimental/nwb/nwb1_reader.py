import h5py
import numpy as np


class NwbReader(object):

    def __init__(self,nwb_file):

        self.nwb_file = nwb_file

    def get_sweep_data(self):
        raise NotImplementedError

    def get_sweep_number(self):
        raise NotImplementedError


    def get_sweep_names(self):

        with h5py.File(self.nwb_file, 'r') as f:
            sweep_names = [e for e in f["acquisition/timeseries"].keys()]

        return sweep_names

    def get_pipeline_version(self):
        """ Returns the AI pipeline version number, stored in the
            metadata field 'generated_by'. If that field is
            missing, version 0.0 is returned.
            Borrowed from the AllenSDK

            Returns
            -------
            int tuple: (major, minor)
        """
        try:
            with h5py.File(self.nwb_file, 'r') as f:
                if 'generated_by' in f["general"]:
                    info = f["general/generated_by"]
                    # generated_by stores array of keys and values
                    # keys are even numbered, corresponding values are in
                    #   odd indices
                    for i in range(len(info)):
                        val = info[i]
                        if info[i] == 'version':
                            version = info[i+1]
                            break
            toks = version.split('.')
            if len(toks) >= 2:
                major = int(toks[0])
                minor = int(toks[1])
        except:
            minor = 0
            major = 0
        return major, minor


class NwbPipelineReader(NwbReader):
    """
    Reads data from the NWB file generated by the ephys pipeline by converting the original NWB generated by MIES.
    """
    def __init__(self, nwb_file):
        NwbReader.__init__(self, nwb_file)




class NwbMiesReader(NwbReader):
    """
    Reads data from the MIES generated NWB file
    """
    def __init__(self, nwb_file):
        NwbReader.__init__(self, nwb_file)

    def get_acquisition(self, sweep_number):

        with h5py.File(self.nwb_file, 'r') as f:
            sweep = f['acquisition']['timeseries']["data_%05d_AD0" % sweep_number]
            data = sweep["data"].value
            rate = 1.0 * sweep["starting_time"].attrs['rate']
            unit = sweep["data"].attrs["unit"]
            conversion = sweep["data"].attrs["conversion"]
            source = sweep.attrs['source']
            ancestry = sweep.attrs["ancestry"]

            stimulus_description_raw = sweep["stimulus_description"].value
            stimulus_description = str(stimulus_description_raw[0])

            if "CurrentClamp" in ancestry[-1]:
                clamp_mode  = "current_clamp"
            elif "VoltageClamp" in ancestry[-1]:
                clamp_mode = "voltage_clamp"
            else:
                raise ValueError("Unknown clamp mode")

            return {
                "data": data,
                "rate": rate,
                "unit": unit,
                "conversion": conversion,
                "clamp_mode": clamp_mode,
                "stimulus_description" : stimulus_description,
                "source": source
                }

    def get_stimulus(self, sweep_number):

        with h5py.File(self.nwb_file, 'r') as f:
            sweep = f['stimulus']['presentation']["data_%05d_DA0" % sweep_number]
            data = sweep["data"].value

            unit = sweep["data"].attrs["unit"]
            rate = 1.0 * sweep["starting_time"].attrs['rate']
            conversion = sweep["data"].attrs["conversion"]
            source = sweep.attrs['source']

            ancestry = sweep.attrs["ancestry"]

            if "CurrentClamp" in ancestry[-1]:
                clamp_mode  = "current_clamp"
            elif "VoltageClamp" in ancestry[-1]:
                clamp_mode = "voltage_clamp"
            else:
                raise ValueError("Unknown clamp mode")

        return {
                "data": data,
                "rate": rate,
                "unit": unit,
                "conversion": conversion,
                "clamp_mode": clamp_mode,
                "source": source
                }



    def get_sweep_number(self,sweep_name):

        sweep_number = int(sweep_name.split('_')[1])

        return sweep_number


def create_nwb_reader(nwb_file):
    """Create an appropriate reader of the nwb_file

    Parameters
    ----------
    nwb_file: str file name

    Returns
    -------
    reader object
    """

    with h5py.File(nwb_file, 'r') as f:
        sweep_names = [e for e in f["acquisition/timeseries"].keys()]
        sweep_naming_convention = sweep_names[0].split('_')[0]

    if sweep_naming_convention =="data":
        return NwbMiesReader(nwb_file)
    elif sweep_naming_convention=="Sweep":
        return NwbPipelineReader(nwb_file)
    else:
        raise ValueError("Unknown sweep naming convention")




