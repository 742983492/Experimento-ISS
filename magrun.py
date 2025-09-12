import RM3100 as mag
import sys
import time
import os
import subprocess
import gc
import csv
import psutil
import numpy as np
import MCP9808 as mcp


def main():
    """Main execution function.

    Performs the following steps:
        - Parses command-line arguments.
        - Initializes logging.
        - Launches magnetometers.
        - Measures data, saves it to CSV files, and compresses them.

    Steps:
    1. Sets up command-line arguments and initializes the logging system.
    2. Launches RM3100 magnetometers and prepares for measurements.
    3. Performs continuous measurement and saves data incrementally.
    4. Compresses the measurement log at the end.

    Args:
        None.

    Returns:
        None.
    """
    userbus, duration, length = parse_arguments()
    maglog, maglog_path, savepath = initialize_logging(duration)
    magnetometers = launch_magnetometers(userbus, maglog)
    temperature = launch_tempsensors(userbus, maglog)
    measure_and_save(magnetometers, temperature, duration, length, savepath, maglog)

    maglog.close()
    compress_file_keep(maglog_path,0)


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
    if len(sys.argv) < 3:
        raise ValueError("Insufficient arguments. Provide bus number and measurement duration.")

    userbus = int(sys.argv[1])
    duration = int(sys.argv[2])

    inputlength = duration
    if len(sys.argv) == 4:
        inputlength = int(sys.argv[3])
        if inputlength > duration:
            inputlength = duration

    return userbus, duration, min(inputlength, 10800)


def initialize_logging(duration):
    """Initialize logging and return log file and paths.

    Generates a timestamped log file in the user's `Documents/MAG/` directory.

    Args:
        duration (int): Total measurement duration in seconds.

    Returns:
        tuple:
            - start (float): Measurement start time (UNIX timestamp).
            - maglog (file): Opened log file for writing logs.
            - maglog_path (str): Path to the log file.

    Notes:
        - Logs initial measurement settings.
    """
    start = time.time()
    strstart = time.strftime("%Y%m%d_%H%M%S", time.gmtime(start))

    mainfolder=os.path.expanduser(f'~/Documents/MAG/')

    os.makedirs(mainfolder, exist_ok=True)  # Ensure the folder exists

    number_files_main=mag.next_numeric_prefix(mainfolder)

    savepath=os.path.expanduser(mainfolder+f'{number_files_main}_{strstart}_{duration}/')

    os.makedirs(savepath, exist_ok=True)  # Ensure the folder exists

    maglog_path = os.path.expanduser(savepath+f'maglog_{strstart}_{duration}s.txt')

    maglog = open(maglog_path, 'w')

    mag.printlog(f"MagnetometerLog started at {time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(start))}", maglog)
    mag.printlog(f"Measurement time: {duration} seconds\n", maglog)

    return maglog, maglog_path, savepath


def launch_magnetometers(userbus, maglog):
    """Launch RM3100 magnetometers.

    Initializes each magnetometer with predefined settings.

    Args:
        userbus (int): The I2C bus number.
        maglog (file): Log file for capturing initialization logs.

    Returns:
        list: A list of RM3100 magnetometer objects.
    """
    addresses = [0x20, 0x21, 0x22, 0x23]
    # addresses = [0x20, 0x22]
    # addresses = [0x23]
    
    frq=0x96    
    cycles=800
    return [mag.launch(userbus, addr, frq, cycles, maglog) for addr in addresses]

def launch_tempsensors(userbus, maglog):
    """Launch Temperature sensors.

    Initializes each magnetometer with predefined settings. Addresses must be in the same order as the magnetometers

    Args:
        userbus (int): The I2C bus number.
        maglog (file): Log file for capturing initialization logs.

    Returns:
        list: A list of Temperature sensors objects.
    """
    # addresses = [0x20, 0x21, 0x22, 0x23]
    addresses = [0x18, 0x19, 0x1a, 0x1b]

    return [mcp.launch(userbus,addr,maglog) for addr in addresses]



def measure_and_save(magnetometers, temperature, duration, length, folder, maglog):
    """
    Perform continuous segmented measurements with multiple magnetometers and save the results.

    This function manages the measurement and saving process in segmented intervals. After each segment,
    it triggers a file compression task for the generated data. Memory usage is monitored and reclaimed
    periodically using explicit garbage collection.

    Args:
        magnetometers (list): List of initialized RM3100 magnetometer objects.
        duration (int): Total measurement duration in seconds.
        length (int): Maximum duration of each measurement segment in seconds.
        folder (str): Base folder path to save the measurement data and compressed files.
        maglog (file): Log file object for recording events and memory usage.

    Returns:
        None
    """
    elapsed_time = 0  # Tracks total elapsed measurement time
    filepaths = []    # List to store paths of generated files

    # Define the save folder for this segment
    savefolderpath=folder
    # os.makedirs(savefolderpath, exist_ok=True)  # Ensure the folder exists

    #list of files
    file_list=list()

    while elapsed_time < duration:

        # Calculate the duration for the current segment
        segment_duration = min(length, duration - elapsed_time)

        # Perform the measurement and save data to files
        filepaths = mag.measure_and_save_cont_MAGTEMP(magnetometers, temperature, segment_duration, maglog, savefolderpath)

        if len(magnetometers)<2:
            file_list.append(filepaths)
        else:
            file_list.extend(filepaths)

        # # Trigger the file compression task for the generated files
        # compress_files_with_script(filepaths, folder, maglog)

        # Trigger the file compression task for the generated files
        if len(file_list)>16 or segment_duration<length:
            compress_files_with_script(file_list, folder, maglog)
            file_list=list()

        # Explicit garbage collection to avoid memory leaks
        gc.collect()

        # Log current memory usage
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        mag.printlog(f"Current memory usage: {memory_usage:.2f} MB", maglog)

        # Update the elapsed time
        elapsed_time += segment_duration
        mag.printlog(f"Remaining time: {duration-elapsed_time} seconds\n", maglog)


def compress_files_with_script(file_list, rootpath, maglog):
    """
    Launch a compression script to compress binary files.
    """
    # Generate a timestamped file path
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    txt_path = rootpath + f"files_to_compress_{timestamp}.txt"
    write_filenames_to_txt(file_list, txt_path,maglog)

    try:
        # Call the compression script
        subprocess.Popen(
            ["python3", "compress_script.py", txt_path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        mag.printlog(f"Compression script launched with file list: {txt_path}\n", maglog)
    except Exception as e:
        mag.printlog(f"Failed to launch compression script: {e}", maglog)
    

def write_filenames_to_txt(file_list, txt_path, maglog):
    """
    Write a list of filenames to a text file.
    """
    try:
        with open(txt_path, 'w') as f:
            for filename in file_list:
                f.write(filename + '\n')
        mag.printlog(f"File list written to {txt_path}", maglog)
    except Exception as e:
        mag.printlog(f"Failed to write file list to {txt_path}: {e}", maglog)


def compress_file_keep(file_path, maglog):
    """Compress a file using xz compression. Keep original file.

    Args:
        file_path (str): Path to the file to compress.
        device_address (int or None): Device address for logging purposes.
        maglog (file): The log file object for logging events.
    """
    if maglog!=0:
        try:
            subprocess.run(['xz', '-9vk', file_path], check=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            mag.printlog(f"File compressed: {file_path}.xz\n", maglog)
        except Exception as e:
            mag.printlog(f"Failed to compress {file_path}: {e}\n", maglog)
    else:
        try:
            subprocess.run(['xz', '-9vk', file_path], check=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"File compressed: {file_path}.xz\n")
        except Exception as e:
            print(f"Failed to compress {file_path}: {e}\n")        


def compress_file_delete(file_path, maglog):
    """Compress a file using xz compression. Delete original file after compression.

    Args:
        file_path (str): Path to the file to compress.
        device_address (int or None): Device address for logging purposes.
        maglog (file): The log file object for logging events.
    """
    if maglog!=0:
        try:
            subprocess.run(['xz', '-9v', file_path], check=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            mag.print(f"File compressed: {file_path}.xz\n", maglog)
        except Exception as e:
            mag.printlog(f"Failed to compress {file_path}: {e}\n", maglog)
    else:
        try:
            subprocess.run(['xz', '-9v', file_path], check=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"File compressed: {file_path}.xz\n")
        except Exception as e:
            print(f"Failed to compress {file_path}: {e}\n")   


if __name__ == "__main__":
    main()
