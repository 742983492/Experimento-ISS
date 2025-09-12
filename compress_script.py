import os
import sys
import subprocess



def compress_files_with_xz(txt_file_path):
    """
    Compress files listed in a text file using `xz` and delete the text file after processing.

    Args:
        txt_file_path (str): Path to the text file containing the list of files to compress.
    """
    try:
        with open(txt_file_path, 'r') as f:
            files_to_compress = [line.strip() for line in f.readlines()]
        
        for file_path in files_to_compress:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue

            try:
                # Compress the file using xz
                subprocess.run(
                    ['xz', '-9v', file_path],
                    check=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"Compressed: {file_path} -> {file_path}.xz")

            except subprocess.CalledProcessError as e:
                print(f"Error compressing {file_path} with xz: {e}")

        # Delete the text file after successful processing
        os.remove(txt_file_path)
        print(f"Deleted text file: {txt_file_path}")

    except FileNotFoundError:
        print(f"Text file not found: {txt_file_path}")
    except Exception as e:
        print(f"Error processing text file {txt_file_path}: {e}")


def compress_batch_files_with_xz(txt_file_path, archive_path):
    """
    Compress files listed in a text file using `xz` and delete the text file after processing.

    Args:
        txt_file_path (str): Path to the text file containing the list of files to compress.
    """
    compresslog_path=os.path.dirname(txt_file_path)
    compresslog = open(compresslog_path + '/' + 'compresslog.txt', 'a')

    files_to_compress=list()

    try:
        with open(txt_file_path, 'r') as f:
            files_in_list = [line.strip() for line in f.readlines()]
        
        for file_path in files_in_list:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}", file=compresslog)
            else:
                files_to_compress.append(file_path)

        print(f"Starting Compression: {archive_path}", file=compresslog)

        # '-c' create, '-J' filter through xz, '-f' output filename
        cmd = ['tar', '-cJf', archive_path, '--remove-files'] + files_to_compress

        try:
            # Compress the file using xz
            subprocess.run(
                cmd,
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"Compressed: {archive_path}", file=compresslog)

        except subprocess.CalledProcessError as e:
            print(f"Error compressing {file_path} with xz: {e}", file=compresslog)

        # Delete the text file after successful processing
        os.remove(txt_file_path)
        print(f"Deleted text file: {txt_file_path}", file=compresslog)

    except FileNotFoundError:
        print(f"Text file not found: {txt_file_path}", file=compresslog)
    except Exception as e:
        print(f"Error processing text file {txt_file_path}: {e}", file=compresslog)


def compress_files_with_zstd(txt_file_path):
    """
    Compress files listed in a text file using `zstd` and delete the text file after processing.

    Args:
        txt_file_path (str): Path to the text file containing the list of files to compress.
    """
    try:
        with open(txt_file_path, 'r') as f:
            files_to_compress = [line.strip() for line in f.readlines()]
        
        for file_path in files_to_compress:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue

            try:
                # Compress the file using xz
                subprocess.run(
                    ['zstd', '-9', '-T0', '--rm', file_path],
                    check=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"Compressed: {file_path} -> {file_path}.xz")

            except subprocess.CalledProcessError as e:
                print(f"Error compressing {file_path} with xz: {e}")

        # Delete the text file after successful processing
        os.remove(txt_file_path)
        print(f"Deleted text file: {txt_file_path}")

    except FileNotFoundError:
        print(f"Text file not found: {txt_file_path}")
    except Exception as e:
        print(f"Error processing text file {txt_file_path}: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 compress_script.py <file_list.txt>")
        sys.exit(1)

    txt_file_path = sys.argv[1]
    if len(sys.argv) == 3:
        archive_path=sys.argv[2]
        compress_batch_files_with_xz(txt_file_path, archive_path)
    else: 
        compress_files_with_xz(txt_file_path)
