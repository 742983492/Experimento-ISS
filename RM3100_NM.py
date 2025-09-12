import time
from smbus import SMBus
import random
import numpy as np
import os
import csv
import re


class RM3100:
    """Class to interface with the RM3100 magnetometer."""
    def __init__(self, userbus, i2c_address):
        """Initialize an RM3100 magnetometer instance.

        Args:
            userbus (int): I2C bus number for the magnetometer.
            i2c_address (int): Magnetometer's I2C address.
            maglog (file): Log file for capturing initialization events.

        Notes:
            - Logs success or failure of I2C initialization.
        """
        try:
            self.i2cbus = SMBus(userbus)
            self.i2c_address = i2c_address
            print(f'{hex(i2c_address)}\tBus {userbus} initialized for magnetometer')
        except Exception as error:
            print(f'{hex(i2c_address)}\tBus {userbus} failed to initialize (SMBus error).\t{error}')

    def read8(self, reg):
        """Read an 8-bit value from a register.

        Args:
            reg (int): Register address to read.
            maglog (file): Log file for capturing errors.

        Returns:
            int or bool: The value read (int) or False if the read fails.

        Notes:
            - Handles I2C communication errors gracefully.
        """
        try:
            return self.i2cbus.read_byte_data(self.i2c_address, reg & ~0x80)
        except Exception as error:
            print(f'Failed to read8 {hex(reg)} register. {error}')
            return False
        
    def read16(self, reg):
        """Read a 16-bit value from a register.

        Args:
            reg (int): Register address to read.
            maglog (file): Log file for capturing errors.

        Returns:
            int or bool: The value read (little-endian) or False if the read fails.
        """
        try:
            # Read a 16-bit word from the register
            value = self.i2cbus.read_word_data(self.i2c_address, reg & ~0x80)
            # Convert the big-endian byte order to little-endian
            bval = value.to_bytes(2, 'big')
            return int.from_bytes(bval, 'little')
        except Exception as error:
            # Log the error and return False to indicate failure
            print(f'Failed to read16 {hex(reg)} register. {error}')
            return False

    def write8(self, reg, value):
        """Write an 8-bit value to the specified register.

        Args:
            reg (int): The register address to write to.
            value (int): The 8-bit value to write.
            maglog (file): Log file object for logging any errors.

        Returns:
            bool: True if the write was successful, False otherwise.
        """
        try:
            # Write an 8-bit value to the register
            self.i2cbus.write_byte_data(self.i2c_address, reg, value)
            return True
        except Exception as error:
            # Log the error and return False to indicate failure
            print(f'Failed to write8 {hex(reg)} register. {error}')
            return False

    def write16(self, reg, value):
        """Write a 16-bit value to the specified register.

        Args:
            reg (int): The register address to write to.
            value (int): The 16-bit value to write.
            maglog (file): Log file object for logging any errors.

        Returns:
            bool: True if the write was successful, False otherwise.
        """
        try:
            # Convert the 16-bit value to big-endian format
            bval = value.to_bytes(2, 'big')
            # Write the big-endian value as little-endian to the register
            self.i2cbus.write_word_data(self.i2c_address, reg, int.from_bytes(bval, 'little'))
            return True
        except Exception as error:
            # Log the error and return False to indicate failure
            print(f'Failed to write16 {hex(reg)} register. {error}')
            return False


    # More efficient block read
    def read_measurements(self):
        try:
            # Read all 9 bytes in one I2C transaction
            reg_start = 0x24 # Start of measurement results registers
            measurements = self.i2cbus.read_i2c_block_data(self.i2c_address, reg_start, 9)

            x, y, z = (self._convert_measurement(measurements[i:i+3]) for i in (0, 3, 6))
            return {'x': x, 'y': y, 'z': z}
        except Exception as error:
            print(f'Failed to read measurements: {error}')
            return False
        
    def check_measurement(self):
        """Check if a measurement is available.

        Args:
            maglog (file): Log file object for logging any errors.

        Returns:
            bool: True if a measurement is available, False otherwise.
        """
        value = self.read8(0xB4)
        if value is False:
            print("Failed to read register 0xB4. Measurement check failed. No connection to PNI.")
            return False
        # elif len(bin(value)) == 10:
        if value & 0x80:  # 0x80 is 0b10000000 in binary
            return True
        else:
            return False

    def read_frequency(self):
        """Read the operating frequency of the magnetometer.

        Args:
            maglog (file): Log file object for logging any errors.

        Returns:
            int or bool: The frequency value read from the register, or False if the read failed.
        """
        rfrq = self.read8(0x8B)
        if rfrq is not False:
            print(f'{hex(self.i2c_address)}\tFrequency={rfrq}')
        return rfrq

    @staticmethod
    def _convert_measurement(data):
        """Convert raw measurement data to a signed integer.

        Args:
            data (list): List of raw bytes from the measurement register.

        Returns:
            int: The converted measurement value.
        """
        if data[0] >= 64:
            return int.from_bytes([255] + data, 'big', signed=True)
        return int.from_bytes([0] + data, 'big', signed=True)

    
def launch(userbus, addr, frq, cycles):
    """Initialize and configure an RM3100 magnetometer for measurements.

    Args:
        userbus (int): The I2C bus number to use.
        addr (int): The I2C address of the magnetometer.
        frq (int): The frequency setting (e.g., 1 for 1Hz, or other specific frequency values).
        cycles (int): The cycle count for measurements.
        maglog (file): The log file for recording status and events.

    Returns:
        RM3100: An initialized and configured RM3100 magnetometer object.
    """
    mag = RM3100(userbus, addr)

    # Define register addresses for configuration
    RM3100_REGISTER_CMM = 0x01  # Continuous measurement mode register
    RM3100_REGISTER_CMX = 0x04  # Cycle count register for X-axis
    RM3100_REGISTER_CMY = 0x06  # Cycle count register for Y-axis
    RM3100_REGISTER_CMZ = 0x08  # Cycle count register for Z-axis
    RM3100_REGISTER_TMRC = 0x0B  # Timer register for frequency settings
    RM3100_REGISTER_TEST = 0xB6  # Test register for status check

    RM3100_REGISTER_RCMX = 0x84  # Read Cycle count register for X-axis
    RM3100_REGISTER_RCMY = 0x86  # Read Cycle count register for Y-axi
    RM3100_REGISTER_RCMZ = 0x88  # Read Cycle count register for Z-axi
    RM3100_REGISTER_RTMRC = 0x8B  # Read Timer register for frequency settings

    # Test communication with the magnetometer
    reg = mag.read8(RM3100_REGISTER_TEST)
    if reg is False:
        print("Failed to read register 0xB6. Status test failed. No connection to PNI.")
        raise Exception("Failed to read register 0xB6 (Test). Status test failed. No connection to PNI.")

    mag.write8(RM3100_REGISTER_TMRC, frq)  # Set custom frequency
    mag.write16(RM3100_REGISTER_CMX, cycles)
    mag.write16(RM3100_REGISTER_CMY, cycles)
    mag.write16(RM3100_REGISTER_CMZ, cycles)

    # Read back configuration for verification
    rccx = mag.read16(RM3100_REGISTER_RCMX)  # Read cycle count for X-axis
    rccy = mag.read16(RM3100_REGISTER_RCMY)  # Read cycle count for Y-axis
    rccz = mag.read16(RM3100_REGISTER_RCMZ)  # Read cycle count for Z-axis
    rfrq = mag.read8(RM3100_REGISTER_RTMRC)  # Read frequency

    # Log configuration details
    print(hex(addr)+ '\t' + f'Frequency={rfrq}')
    print(hex(addr)+ '\t' + f'Cycle count X={rccx}')
    print(hex(addr)+ '\t' + f'Cycle count Y={rccy}')
    print(hex(addr)+ '\t' + f'Cycle count Z={rccz}\n')

    # Set continuous measurement mode
    mag.write8(RM3100_REGISTER_CMM, 0x79)

    return mag


def measure_and_save_cont_MAG(mags, duration, save_folder):
    """
    Perform continuous measurement with multiple magnetometers and save results in real-time to CSV files.

    Each magnetometer's data is saved directly to its own CSV file, including a counter to track the number
    of samples. Measurements are logged periodically based on a predefined interval.

    Args:
        mags (list): List of RM3100 magnetometer objects.
        duration (int): Total duration of measurement in seconds.
        save_folder (str): Directory to save the resulting CSV files.

    Returns:
        list: A list of file paths for the CSV files generated.
    """
    # Record the start and finish times for the measurement session
    start = time.time()
    finish = start + duration

    print(f"Measurement starting at {time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(start))} lasting {duration} seconds")

    # Determine the frequency for logging sample points
    sampleprint = 300
    print("DEBUG: sampleprint=", sampleprint)
    print(f"Sample print every {sampleprint} samples\n")

    #Worst case
    rfrq = max(mag.read8(0x8B) for mag in mags)
    worstfreq = int(1.1*round(rfrq)/3)
    worstcounter=worstfreq*duration

    # Prepare file paths, counters, and CSV writers
    file_paths = []
    counters = []
    writers = []  # Store file writer objects for each magnetometer

    # Initialize file paths, counters, and CSV writers
    for mag in mags:
        magaddr = hex(mag.i2c_address)
        file_path = os.path.join(save_folder, f"mag_{magaddr}_{time.strftime('%Y%m%d_%H%M%S', time.gmtime(start))}.csv")
        file_paths.append(file_path)
        counters.append(0)  # Initialize counter to start from 0

        # Open the file and initialize the CSV writer
        f = open(file_path, 'w', newline='')
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Counter", "X", "Y", "Z"])  # Header row
        writers.append((f, writer))  # Store file object and writer together
        print(f"Initialized CSV for {magaddr}: {file_path}")

    pretime = time.time() - start

    # Main measurement loop


    while time.time() <= finish + pretime:
        for i, mag in enumerate(mags):
            if mag.check_measurement() and counters[i]<worstcounter:  # Check if data is ready and counter is less than worst case
                try:
                    # Perform measurement
                    timestamp = time.time()
                    mag_data = mag.read_measurements()
                    x = mag_data['x']
                    y = mag_data['y']
                    z = mag_data['z']
                    
                    # Write the measurement directly to the CSV file
                    #_, writer = writers[i]  # Retrieve writer for the current magnetometer
                    #writer.writerow([timestamp, counters[i], x, y, z])
                    print(f"{timestamp:.6f}, {counters[i]}, X={x}, Y={y}, Z={z}")

                    # Log the sample if it matches the print interval
                    if counters[i] % sampleprint == 0:
                        print(f"{hex(mag.i2c_address)}\t{counters[i]}\tX={x}\t\tY={y}\t\tZ={z}")

                    # Clean up temporary data
                    del mag_data

                    # Increment counter
                    counters[i] += 1

                except Exception as e:
                    print(f"Error during measurement or file writing for magnetometer {hex(mag.i2c_address)}: {e}")

    # Close all open files
    for f, _ in writers:
        f.close()

    print("Measurement completed.")
    return file_paths



def next_numeric_prefix(folder, width=3, mag_id=None):
    """
    Returns the next index zero-padded to `width` digits.
    If mag_id is None, counts all entries; otherwise only those whose
    name starts with 'mag_<mag_id>_'.
    """

    entries = [name for name in os.listdir(folder) if not name.startswith('.')]
    if mag_id is not None:
        mag_id_str=f"{mag_id}"
        entries = [f for f in entries if mag_id_str in f]
    n = len(entries)
    return str(n + 1).zfill(width)

