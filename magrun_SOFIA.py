import RM3100_SOFIA as mag
import sys
import time
import os
import subprocess
import gc
import csv
import psutil
import numpy as np



def main():
    userbus, duration = parse_arguments() # duration = length, userbus = 1
    magnetometers = launch_magnetometers(userbus)
    measure(magnetometers, duration)



    def parse_arguments():
        """Parse and validate command-line arguments.

        Inputs:
            Command-line arguments from `sys.argv`:
                - `sys.argv[1]`: Bus number (int).
                - `sys.argv[2]`: Duration of measurement in seconds (int).
                - `sys.argv[3]` (optional): Length of each measurement file in seconds (int).

        Returns:
            tuple:
                - userbus (int): The I2C bus number.
                - duration (int): Total duration of measurement.
                - length (int): Duration per measurement file, capped at 3600 seconds.

        Raises:
            ValueError: If required arguments are missing or invalid.
        """
    if len(sys.argv) < 3:  # Revisa que haya suficientes argumentos
        raise ValueError("Insufficient arguments. Provide bus number and measurement duration.")

    userbus = int(sys.argv[1])
    duration = int(sys.argv[2])

    return userbus, duration



def launch_magnetometers(userbus):
    """Launch RM3100 magnetometers.

    Initializes each magnetometer with predefined settings.

    Args:
        userbus (int): The I2C bus number. -> 1
        maglog (file): Log file for capturing initialization logs.

    Returns:
        list: A list of RM3100 magnetometer objects.
    """
    addresses = [0x20]  # por ahora solo dejar 0x20
    # addresses = [0x20, 0x21, 0x22, 0x23]
    
    frq=0x96   # frecuencia 150 hz limitada por los cycles 
    cycles=800
    return [mag.launch(userbus, addr, frq, cycles) for addr in addresses]  # inicia los magnetometros



def measure(magnetometers, duration): 
    """
    Perform continuous segmented measurements with multiple magnetometers.

    Args:
        magnetometers (list): List of initialized RM3100 magnetometer objects.
        duration (int): Total measurement duration in seconds.
    Returns:
        None
    """
    elapsed_time = 0  # Tracks total elapsed measurement time
    filepaths = []    # List to store paths of generated files

    #list of files
    file_list=list()

    while elapsed_time < duration:

        # Calculate the duration for the current segment
        segment_duration = duration - elapsed_time

        # Perform the measurement and save data to files
        filepaths = mag.measure_MAG(magnetometers, segment_duration)

        if len(magnetometers)<2:
            file_list.append(filepaths)
        else:
            file_list.extend(filepaths)

        # Log current memory usage
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        print(f"Current memory usage: {memory_usage:.2f} MB")

        # Update the elapsed time
        elapsed_time += segment_duration
        print(f"Remaining time: {duration-elapsed_time} seconds\n")



if __name__ == "__main__":
    main()
