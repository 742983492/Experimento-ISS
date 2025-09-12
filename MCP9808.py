#!/usr/bin/env python
from smbus import SMBus
import time
import RM3100 as mag

class MCP9808:
    """
    Class to interface with the MCP9808 temperature sensor.

    This class provides methods for initializing, reading temperature data,
    and checking sensor status using the I2C protocol.

    Attributes:
        i2cbus (SMBus): I2C communication bus object.
        i2c_address (int): I2C address of the MCP9808 sensor.
    """

    def __init__(self, userbus, i2c_address, maglog):
        """
        Initialize an MCP9808 temperature sensor instance.

        Args:
            userbus (int): I2C bus number the sensor is connected to.
            i2c_address (int): The I2C address of the MCP9808 sensor.
            maglog (file): Log file object for recording initialization events.

        Notes:
            - Logs successful initialization or failure due to SMBus errors.
        """
        try:
            self.i2cbus = SMBus(userbus)
            self.i2c_address = i2c_address
            mag.printlog(f'{hex(i2c_address)}\tBus {userbus} initialized for Temperature Sensors\n', maglog)
        except Exception as error:
            mag.printlog(f'{hex(i2c_address)}\tBus {userbus} failed to initialize (SMBus error).\t{error}', maglog)

    def read16(self, reg, maglog):
        """
        Read a 16-bit value from a specified register.

        Args:
            reg (int): Register address to read from.

        Returns:
            int: The 16-bit value read from the register (little-endian format).

        Notes:
            - Converts data from big-endian to little-endian before returning.
        """
        try:
            value = self.i2cbus.read_word_data(self.i2c_address, reg & ~0x80)
            bval = value.to_bytes(2, 'big')  # Convert to byte array
            return int.from_bytes(bval, 'little')  # Convert to little-endian integer
        except Exception as e:
            mag.printlog(f"{hex(self.i2c_address)}\tError reading 16-bit register {hex(reg)}: {e}",maglog)
            return None
    
    def read_temp(self,maglog):
        """
        Read and return the temperature from the MCP9808 sensor.

        Returns:
            float: Temperature in degrees Celsius.

        Notes:
            - The temperature is read from register 0x05.
            - The raw 16-bit data is processed to extract the temperature.
            - The sensor uses a 13-bit signed format where:
                - Bits [12:0] represent temperature data.
                - Bit [12] is the sign bit (0 = positive, 1 = negative).
            - Negative temperatures are converted using 2's complement.
        """
        try:
            value = self.i2cbus.read_word_data(self.i2c_address, 0x05)
            bval = value.to_bytes(2, 'big')  # Convert raw data to byte array
            ivalue = int.from_bytes(bval, 'little')  # Convert to integer

            # Extract relevant temperature bits
            temp = ivalue & 0x1FFF  # 13-bit temperature value
            l_temp = temp & 0x00FF   # Lower 8 bits
            h_temp = temp & 0xFF00   # Higher 8 bits
            sign = temp & 0x1000     # Check if negative

            # Convert raw register data to a floating point temperature value
            if sign == 0:
                return float(h_temp >> 4) + float(l_temp) * 2**-4
            else:
                return (float(h_temp >> 4) + float(l_temp) * 2**-4) - 512
        except Exception as e:
            mag.printlog(f"{hex(self.i2c_address)}\tError reading temperature: {e}",maglog)
            return None
    
    def check_masurement(self,maglog):
        """
        Check the measurement status of the sensor.

        Returns:
            bool: True if the sensor is operational and responding correctly, False otherwise.

        Notes:
            - Reads status registers 0x06 and 0x07.
            - Expected values: Register 0x06 = 84, Register 0x07 = 1024.
            - If these values match, the sensor is assumed to be functioning correctly.
        """
        try:
            value1 = self.read16(0x06,maglog)
            value2 = self.read16(0x07,maglog)

            if value1 == 84 and value2 == 1024:
                return True
            return False
        except Exception as e:
            mag.printlog(f"{hex(self.i2c_address)}\t Error checking measurement status: {e}",maglog)
            return False

def launch(userbus, addr, maglog):
    """
    Create and return an MCP9808 sensor instance.

    Args:
        userbus (int): I2C bus number the sensor is connected to.
        addr (int): I2C address of the sensor.
        maglog (file): Log file object for recording initialization events.

    Returns:
        MCP9808: An instance of the MCP9808 class.
    """
    return MCP9808(userbus, addr, maglog)

