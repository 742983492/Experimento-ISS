import time
from smbus import SMBus

class RM3100:
    """Class to interface with the RM3100 magnetometer."""
    def __init__(self, userbus, i2c_address): # userbus es 1 (se ingresa en la terminal -y 1)
        """Initialize an RM3100 magnetometer instance.

        Args:
            userbus (int): I2C bus number for the magnetometer.
            i2c_address (int): Magnetometer's I2C address.
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

        Returns:
            int or bool: The value read (int) or False if the read fails.
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

    def read_measurements(self):
        try:
            # Read all 9 bytes in one I2C transaction
            reg_start = 0x24 # Start of measurement results registers
            measurements = self.i2cbus.read_i2c_block_data(self.i2c_address, reg_start, 9)

            def convert3bytes(data):
                if data[0] >= 64:  # si el MSB >= 0x40, entonces es un número negativo
                    return int.from_bytes([255] + data, 'big', signed=True)
                else:            # si no, es positivo
                    return int.from_bytes([0] + data, 'big', signed=True)
                
            x = convert3bytes(measurements[0:3])
            y = convert3bytes(measurements[3:6])
            z = convert3bytes(measurements[6:9])

            return {'x': x, 'y': y, 'z': z}
        except Exception as error:
            print(f'Failed to read measurements: {error}')
            return False
        

    def check_measurement(self):
        """Check if a measurement is available.

        Args:

        Returns:
            bool: True if a measurement is available, False otherwise.
        """
        value = self.read8(0xB4)
        if value is False:
            print("Failed to read register 0xB4. Measurement check failed. No connection to PNI.")
            return False
        if value & 0x80:  # 0x80 is 0b10000000 in binary
            return True
        else:
            return False




def launch(userbus, addr, frq, cycles):
    """Initialize and configure an RM3100 magnetometer for measurements.

    Args:
        userbus (int): The I2C bus number to use.
        addr (int): The I2C address of the magnetometer.
        frq (int): The frequency setting (e.g., 1 for 1Hz, or other specific frequency values).
        cycles (int): The cycle count for measurements.

    Returns:
        RM3100: An initialized and configured RM3100 magnetometer object.
    """
    mag = RM3100(userbus, addr)

    # Define register addresses for configuration
    RM3100_REGISTER_CMM   = 0x01  # Registro de modo de medición (0x79 = iniciar medición continua)
    RM3100_REGISTER_CMX   = 0x04  # Configura cuántos ciclos usar en el eje X
    RM3100_REGISTER_CMY   = 0x06  # Configura cuántos ciclos usar en el eje Y
    RM3100_REGISTER_CMZ   = 0x08  # Configura cuántos ciclos usar en el eje Z
    RM3100_REGISTER_TMRC  = 0x0B  # Configura la frecuencia de muestreo (Timer Register)
    RM3100_REGISTER_TEST  = 0xB6  # Registro de prueba: verificar comunicación con el chip

    # Read-back registers (para leer y confirmar lo configurado)
    RM3100_REGISTER_RCMX  = 0x84  # Lee el valor actual de RM3100_REGISTER_CMX (ciclos X)
    RM3100_REGISTER_RCMY  = 0x86  # Lee el valor actual de RM3100_REGISTER_CMY (ciclos Y)
    RM3100_REGISTER_RCMZ  = 0x88  # Lee el valor actual de RM3100_REGISTER_CMZ (ciclos Z)
    RM3100_REGISTER_RTMRC = 0x8B  # Lee el valor actual de RM3100_REGISTER_TMRC (frecuencia)

    # Test communication with the magnetometer
    reg = mag.read8(RM3100_REGISTER_TEST)
    if reg is False:
        print("Failed to read register 0xB6. Status test failed. No connection to PNI.")
        raise Exception("Failed to read register 0xB6 (Test). Status test failed. No connection to PNI.")

    mag.write8(RM3100_REGISTER_TMRC, frq)  # Establece frecuencia en el registro creado anteriormente
    mag.write16(RM3100_REGISTER_CMX, cycles)  # Establece ciclos en X en el registro creado anteriormente
    mag.write16(RM3100_REGISTER_CMY, cycles)  # Establece ciclos en Y en el registro creado anteriormente
    mag.write16(RM3100_REGISTER_CMZ, cycles)  # Establece ciclos en Z en el registro creado anteriormente

    # Lee las configuraciones para verificar que estén correctas
    rccx = mag.read16(RM3100_REGISTER_RCMX)  # Read cycle count for X-axis
    rccy = mag.read16(RM3100_REGISTER_RCMY)  # Read cycle count for Y-axis
    rccz = mag.read16(RM3100_REGISTER_RCMZ)  # Read cycle count for Z-axis
    rfrq = mag.read8(RM3100_REGISTER_RTMRC)  # Read frequency

    # Muestra las configuraciones para cada sensor (uno solo por ahora)
    print(hex(addr)+ '\t' + f'Frequency={rfrq}')
    print(hex(addr)+ '\t' + f'Cycle count X={rccx}')
    print(hex(addr)+ '\t' + f'Cycle count Y={rccy}')
    print(hex(addr)+ '\t' + f'Cycle count Z={rccz}\n')

    # Set continuous measurement mode
    mag.write8(RM3100_REGISTER_CMM, 0x79)  # el sensor arranca en modo continuo midiendo X, Y, Z.

    return mag


def measure_MAG(mags, duration):
    start = time.time()
    finish = start + duration
    counters = [0 for _ in mags] 

    print(f"Measurement starting at {time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(start))} lasting {duration} seconds")

    print("Timestamp\tI2C Address\tSample Count\tX\tY\tZ")
    sampleprint = 300
    pretime = time.time() - start

    # Main measurement loop

    while time.time() <= finish + pretime:
        for i, mag in enumerate(mags):
            if mag.check_measurement():
                timestamp = time.time()
                mag_data = mag.read_measurements()
                if mag_data:  
                    counters[i] += 1
                    if counters[i] % sampleprint == 0:  
                        x, y, z = mag_data['x'], mag_data['y'], mag_data['z']
                        print(f"{timestamp:.6f}\t{hex(mag.i2c_address)}\t{counters[i]}\tX={x}\tY={y}\tZ={z}")
                    time.sleep(0.001)

    print("Measurement completed.")
