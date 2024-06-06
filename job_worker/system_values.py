import pandas as pd
import cpuinfo
import psutil
import geocoder
from constant import GB

def get_system_values():
    # number of logical core
    core_num = cpuinfo.get_cpu_info()['count']

    # Get memory size in GB
    mem_num = psutil.virtual_memory().total / GB

    # Get carbon intensity for the current location
    g = geocoder.ip('me')
    CI_data = pd.read_csv('./CI_aggregated.csv')
    country = g.country
    CI = float((CI_data.query('index == @country')['in gCO2e/kWh']).values[0])

    # Save values to a file
    return {
        "core_num": core_num,
        "core_power": 28, # TDP
        "mem_num": mem_num,
        "mem_power": 0.3725,
        "PUE": 1.67,
        "CI": CI
    }
