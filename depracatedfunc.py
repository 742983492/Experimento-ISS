
#FROM RM3100

def measure_cont(mags, duration, maglog):
    """Continuous measurement for multiple magnetometers.

    Args:
        mags (list): List of RM3100 magnetometer objects.
        duration (int): Duration of measurement in seconds.
        maglog (file): Log file for logging events.

    Returns:
        list: A list of dictionaries containing timestamp and measurements for each magnetometer.
    """
    # Record the start and finish times for the measurement session
    start = time.time()
    finish = start + duration

    printlog(f'Measurement starting at {time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(start))} lasting {duration} seconds', maglog)

    #Worst case
    rfrq = max(mag.read8(0x8B, maglog) for mag in mags)
    worstfreq = int(1.1*round(rfrq)/3)
    worstvect=worstfreq*duration

    # Prepare results containers for each magnetometer
    results = []
    for mag in mags:
        results.append({
            'x': [],
            'y': [],
            'z': [],
            'timestamp': [],
            'counter': -1,
            'countervector': [],
            'magaddr': hex(mag.i2c_address),
        })
    
    # Determine the frequency for logging sample points
    sampleprint = 1 if sum(mag.read8(0x8B, maglog) for mag in mags) / len(mags) < 140 else int(round((sum(mag.read8(0x8B, maglog) for mag in mags) / len(mags)) / 0.5))
    printlog(f'Sample print every {sampleprint} samples\n', maglog)


    while time.time() <= finish:
        for mag, result in zip(mags, results):
            if mag.check_measurement(maglog):
                # Increment the counter and store timestamp and measurement data
                result['counter'] += 1
                counter = result['counter']
                if counter < worstvect:
                    result['timestamp'].append(time.time())
                    mag_data = mag.read_measurements(maglog)
                    result['x'].append(mag_data['x'])
                    result['y'].append(mag_data['y'])
                    result['z'].append(mag_data['z'])
                    result['countervector'].append(counter+1)

                    # Log the sample if it matches the print interval
                    if counter % sampleprint == 0:
                        printlog(f"{hex(mag.i2c_address)}\t" f"{counter} \t {result['x'][counter]} \t\t {result['y'][counter]} \t\t {result['z'][counter]}", maglog)
                    # Free temporary variable
                    del mag_data

    return results


def measure_cont_test(mags, duration, maglog):
    """Continuous measurement for multiple magnetometers.

    Args:
        mags (list): List of RM3100 magnetometer objects.
        duration (int): Duration of measurement in seconds.
        maglog (file): Log file for logging events.

    Returns:
        list: A list of dictionaries containing timestamp and measurements for each magnetometer.
    """
    # Record the start and finish times for the measurement session
    start = time.time()
    finish = start + duration

    printlog(f'Measurement starting at {time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(start))} lasting {duration} seconds', maglog)

    #Worst case
    rfrq = 150
    worstfreq = int(1.1*round(rfrq)/3)
    worstvect=worstfreq*duration

    # Prepare results containers for each magnetometer
    results = []
    for mag in mags:
        results.append({
            'x': [],
            'y': [],
            'z': [],
            'timestamp': [],
            'counter': -1,
            'countervector': [],
            'magaddr': hex(mag.i2c_address),
        })
    
    # Determine the frequency for logging sample points
    sampleprint = 10000
    printlog(f'Sample print every {sampleprint} samples\n', maglog)


    while time.time() <= finish:
        for mag, result in zip(mags, results):
            result['counter'] += 1
            counter = result['counter']
            result['timestamp'].append(time.time())
            result['x'].append(round((random.random()-0.5)*8388607))
            result['y'].append(round((random.random()-0.5)*8388607))
            result['z'].append(round((random.random()-0.5)*8388607))
            result['countervector'].append(counter+1)

            # Log the sample if it matches the print interval
            if counter % sampleprint == 0:
                printlog(f"{hex(mag.i2c_address)}\t" f"{counter} \t {result['x'][counter]} \t\t {result['y'][counter]} \t\t {result['z'][counter]}", maglog)

    return results

def measure_cont_test_save_cont(mags, duration, maglog, save_folder):
    """
    Continuous measurement for multiple magnetometers with real-time saving to CSV files,
    including a counter vector.

    Args:
        mags (list): List of RM3100 magnetometer objects.
        duration (int): Duration of measurement in seconds.
        maglog (file): Log file for logging events.
        save_folder (str): Folder to save the CSV files.

    Returns:
        None
    """
    # Record the start and finish times for the measurement session
    start = time.time()
    finish = start + duration

    printlog(f'Measurement starting at {time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(start))} lasting {duration} seconds', maglog)

    # Determine the frequency for logging sample points
    sampleprint = 10000
    printlog(f'Sample print every {sampleprint} samples\n', maglog)

    # Prepare lists for file paths and counters
    file_paths = []
    counters = []

    # Initialize file paths and counters for each magnetometer
    for mag in mags:
        magaddr = hex(mag.i2c_address)
        file_path = os.path.join(save_folder, f"mag_{magaddr}_{time.strftime('%Y%m%d_%H%M%S', time.gmtime(start))}.csv")
        file_paths.append(file_path)
        counters.append(-1)  # Initialize counter vector

        # Initialize the CSV file with headers
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Counter", "X", "Y", "Z"])  # Header row
        printlog(f"Initialized CSV for {magaddr}: {file_path}", maglog)
    
    pretime=time.time()-start

    # Main measurement loop
    while time.time() <= finish+pretime:
        for i, mag in enumerate(mags):
            magaddr = hex(mag.i2c_address)

            # Increment counter
            counters[i] += 1

            # Simulate measurement and save directly to CSV
            timestamp = time.time()
            x = round((random.random() - 0.5) * 8388607)
            y = round((random.random() - 0.5) * 8388607)
            z = round((random.random() - 0.5) * 8388607)

            # Write the measurement directly to the CSV file
            with open(file_paths[i], 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, counters[i], x, y, z])

            # Log the sample if it matches the print interval
            if (counters[i]) % sampleprint == 0:
                printlog(f"{hex(mag.i2c_address)}\t" f"{counters[i]} \t {x} \t\t {y} \t\t {z}", maglog)


    printlog("Measurement completed.", maglog)
    return file_paths


#FROM MAGRUN

def measure_and_save_text(magnetometers, duration, length, start_time, folder, maglog):
    """Perform measurements, save results, and compress files.

    Handles periodic measurement, file-saving, and memory management during a long-running measurement session.

    Args:
        magnetometers (list): List of initialized RM3100 magnetometer objects.
        duration (int): Total measurement duration in seconds.
        length (int): Duration of data per file segment in seconds.
        start_time (float): Start time of the measurement (UNIX timestamp).
        folder (str): Base directory for saving output files.
        maglog (file): Log file for recording events.

    Notes:
        - Calls `mag.measure_cont` for concurrent measurements.
        - Periodically compresses files to manage disk usage.
        - Logs system memory usage with `psutil`.
    """
    elapsed_time = 0
    First=True

    while elapsed_time < duration:
        filepaths=[]
        gc.collect()  # Explicit garbage collection
        segment_duration = min(length, duration - elapsed_time)
        segment_start_time = time.time()

        measurements = mag.measure_cont(magnetometers, segment_duration, maglog)

        starttimeS=time.time()
        # Save results to a file
        if First:
            file_time = time.strftime("%Y%m%d_%H%M%S", time.gmtime(start_time))
            filepaths=save_results_to_csv(measurements,file_time,segment_duration,folder,filepaths,maglog)
            First=False
        else:
            file_time = time.strftime("%Y%m%d_%H%M%S", time.gmtime(segment_start_time))
            filepaths=save_results_to_csv(measurements,file_time,segment_duration,folder,filepaths,maglog)
        endttimeS=time.time()

        # Housekeeping to avoid memory leaks
        del measurements
        gc.collect()

        # If we have more than 36 hours of data, compress the whole array of data
        print(len(filepaths),len(magnetometers))
        if len(filepaths) > 36*len(magnetometers):
            starttime=time.time()
            for filenames in filepaths[:-1]:
                compress_file_keep(filenames,maglog)
            filepaths=filepaths[-1:]
            endttime=time.time()
            mag.printlog(f'Time taken to compress during run: {endttime-starttime}',maglog)
        
        # Log memory usage
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        mag.printlog(f"Current memory usage: {memory_usage:.2f} MB", maglog)

        elapsed_time += segment_duration
        mag.printlog(f'Time taken to save: {endttimeS-starttimeS}',maglog)
        mag.printlog(f"Remaining time: {duration-elapsed_time} seconds\n", maglog)


    # Separate loop to compress files after all measurements are done
    starttime=time.time()
    for filenames in filepaths:
        compress_file_keep(filenames,maglog)
    endttime=time.time()
    mag.printlog(f'Time taken to compress end: {endttime-starttime}',maglog)


def save_results_to_text(results, file_time, segment_duration, folder, filenames, maglog):
    """Save measurement data to text files for all magnetometers using `np.savetxt`.

    Args:
        results (list): List of dictionaries containing measurement data for each magnetometer.
        file_time (str): Timestamp for the filenames.
        segment_duration (int): Duration of each measurement segment.
        folder (str): Base directory for saving output files.
        filenames (list): List of previously saved filenames (updated by this function).
        maglog (file): Log file for capturing file-saving logs.

    Returns:
        list: Updated list of filenames, including newly created files.

    Notes:
        - Saves data for each magnetometer into a separate text file.
        - Appends filenames to `filenames` for later processing.
        - Uses NumPy's `np.savetxt` for efficient text-based storage.
    """
    try:
        for result in results:
            magaddr = result['magaddr']  # Unique address for each magnetometer
            file = f"Documents/MAG/mag_{magaddr}_{file_time}_{segment_duration}s.txt"
            save_path = os.path.join(folder, file)
            filenames.append(save_path)

            # Prepare data for saving
            data = np.column_stack([
                result['timestamp'],
                result['countervector'],
                result['x'],
                result['y'],
                result['z'],
            ])

            # Save the data using np.savetxt
            np.savetxt(
                save_path,
                data,
                delimiter=",",
                header="Timestamp,Counter,X,Y,Z",
                comments="",
                fmt=["%f", "%d", "%d", "%d", "%d"]  # Format for each column
            )

            mag.printlog(f"Data saved to {save_path}", maglog)

    except Exception as e:
        mag.printlog(f"Failed to save data to {save_path}: {e}", maglog)

    return filenames


def save_results_to_csv(results, file_time, segment_duration, folder, filenames, maglog):
    """Save measurement data to CSV files for all magnetometers.

    Args:
        results (list): List of dictionaries containing measurement data for each magnetometer.
        file_time (str): Timestamp for the filenames.
        segment_duration (int): Duration of each measurement segment.
        folder (str): Base directory for saving output files.
        filenames (list): List of previously saved filenames (updated by this function).
        maglog (file): Log file for capturing file-saving logs.

    Returns:
        list: Updated list of filenames, including newly created files.

    Notes:
        - Saves data for each magnetometer into a separate CSV file.
        - Appends filenames to `filenames` for later processing.
    """
    # try:
    for result in results:
        magaddr = result['magaddr']  # Unique address for each magnetometer
        file = f"Documents/MAG/mag_{magaddr}_{file_time}_{segment_duration}s.csv"
        save_path = os.path.join(folder, file)
        filenames.append(save_path)

        # Save the data
        with open(save_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Counter", "X", "Y", "Z"])  # CSV Header
            for i in range(len(result['timestamp'])):
                writer.writerow([
                    result['timestamp'][i],
                    result['countervector'][i],
                    result['x'][i],
                    result['y'][i],
                    result['z'][i],
                ])

        mag.printlog(f"Data saved to {save_path}", maglog)

    # except Exception as e:
    #     mag.printlog(f"Failed to save data to {save_path}: {e}", maglog)

    return filenames


def measure_and_save_test(magnetometers, duration, length, start_time, folder, maglog):
    elapsed_time = 0
    First=True
    filepaths=[]

    while elapsed_time < duration:
        gc.collect()  # Explicit garbage collection
        segment_duration = min(length, duration - elapsed_time)
        segment_start_time = time.time()

        measurements = mag.measure_cont_test_(magnetometers, segment_duration, maglog)

        starttimeS=time.time()
        # Save results to a file
        if First:
            file_time = time.strftime("%Y%m%d_%H%M%S", time.gmtime(start_time))
            filepaths=save_results_to_csv(measurements,file_time,segment_duration,folder,filepaths,maglog)
            First=False
        else:
            file_time = time.strftime("%Y%m%d_%H%M%S", time.gmtime(segment_start_time))
            filepaths=save_results_to_csv(measurements,file_time,segment_duration,folder,filepaths,maglog)
        endttimeS=time.time()

        # Trigger compression task
        compress_files_with_script(filepaths, folder, maglog)

        # Housekeeping to avoid memory leaks
        del measurements
        gc.collect()

        # Log memory usage
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        mag.printlog(f"Current memory usage: {memory_usage:.2f} MB", maglog)

        elapsed_time += segment_duration
        mag.printlog(f'Time taken to save: {endttimeS-starttimeS}',maglog)
        mag.printlog(f"Remaining time: {duration-elapsed_time} seconds\n", maglog)


def measure_and_save_binary(magnetometers, duration, length, start_time, folder, maglog):
    """Perform measurements, save results, and compress files.

    Handles periodic measurement, file-saving, and memory management during a long-running measurement session.

    Args:
        magnetometers (list): List of initialized RM3100 magnetometer objects.
        duration (int): Total measurement duration in seconds.
        length (int): Duration of data per file segment in seconds.
        start_time (float): Start time of the measurement (UNIX timestamp).
        folder (str): Base directory for saving output files.
        maglog (file): Log file for recording events.

    Notes:
        - Calls `mag.measure_cont` for concurrent measurements.
        - Periodically compresses files to manage disk usage.
        - Logs system memory usage with `psutil`.
    """
    elapsed_time = 0
    First=True

    while elapsed_time < duration:
        filepaths=[]
        gc.collect()  # Explicit garbage collection
        segment_duration = min(length, duration - elapsed_time)
        segment_start_time = time.time()

        measurements = mag.measure_cont(magnetometers, segment_duration, maglog)

        starttimeS=time.time()
        # Save results to a file
        if First:
            file_time = time.strftime("%Y%m%d_%H%M%S", time.gmtime(start_time))
            filepaths=save_results_to_binary(measurements,file_time,segment_duration,folder,filepaths,maglog)
            First=False
        else:
            file_time = time.strftime("%Y%m%d_%H%M%S", time.gmtime(segment_start_time))
            filepaths=save_results_to_binary(measurements,file_time,segment_duration,folder,filepaths,maglog)
        endttimeS=time.time()

        # Trigger compression task
        compress_files_with_script(filepaths, folder, maglog)

        # Housekeeping to avoid memory leaks
        del measurements
        gc.collect()

        # Log memory usage
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        mag.printlog(f"Current memory usage: {memory_usage:.2f} MB", maglog)

        elapsed_time += segment_duration
        mag.printlog(f'Time taken to save: {endttimeS-starttimeS}',maglog)
        mag.printlog(f"Remaining time: {duration-elapsed_time} seconds\n", maglog)


def save_results_to_binary(results, file_time, segment_duration, folder, filenames, maglog):
    """Save measurement data to binary files for all magnetometers using NumPy's `np.save`.

    Args:
        results (list): List of dictionaries containing measurement data for each magnetometer.
        file_time (str): Timestamp for the filenames.
        segment_duration (int): Duration of each measurement segment.
        folder (str): Base directory for saving output files.
        filenames (list): List of previously saved filenames (updated by this function).
        maglog (file): Log file for capturing file-saving logs.

    Returns:
        list: Updated list of filenames, including newly created files.

    Notes:
        - Saves data for each magnetometer into a separate `.npy` binary file.
        - Appends filenames to `filenames` for later processing.
    """
    try:
        for result in results:
            magaddr = result['magaddr']  # Unique address for each magnetometer
            file = f"Documents/MAG/mag_{magaddr}_{file_time}_{segment_duration}s.npy"
            save_path = os.path.join(folder, file)
            filenames.append(save_path)

            # Prepare data as a structured array
            data = np.array(
                [
                    result['timestamp'],
                    result['countervector'],
                    result['x'],
                    result['y'],
                    result['z'],
                ],
                dtype=object,  # Allow flexibility in storing arrays of varying lengths
            )

            # Save data as a binary file
            np.save(save_path, data)

            mag.printlog(f"Data saved to {save_path}", maglog)

    except Exception as e:
        mag.printlog(f"Failed to save data to {save_path}: {e}", maglog)

    return filenames