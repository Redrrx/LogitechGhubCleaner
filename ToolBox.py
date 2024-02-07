import ctypes
import logging
import re
import winreg
import os
import glob
import asyncio
from datetime import datetime
import aiofiles.os
import colorlog
from tqdm.asyncio import tqdm


async def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


async def unlock_file(file_path: str, forced: bool = False) -> bool:
    absolute_path = os.path.abspath(file_path)
    process = await asyncio.create_subprocess_exec(
        os.path.abspath('handle64.exe'),
        absolute_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if "No matching handles found" in stdout.decode():
        return True

    pids = set(re.findall(r'\spid: (\d+)\s', stdout.decode()))

    if not pids:
        logging.warning("Failed to find locking PIDs.")
        return False

    for pid in pids:
        process_name_cmd = f'tasklist /fi "PID eq {pid}"'
        process_name_process = await asyncio.create_subprocess_shell(
            process_name_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        process_stdout, process_stderr = await process_name_process.communicate()

        if 'explorer.exe' in process_stdout.decode().lower():
            if not forced:
                logging.warning("Skipping termination of critical system process: explorer.exe")
                continue
            else:
                logging.warning("Forced mode is active. Terminating explorer.exe")

        kill_process = await asyncio.create_subprocess_shell(
            f'taskkill /F /PID {pid}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        kill_stdout, kill_stderr = await kill_process.communicate()
        if kill_process.returncode == 0:
            logging.info(f"Successfully terminated process {pid}.")
        else:
            logging.error(f"Failed to terminate process {pid}. Output: {kill_stderr.decode()}")
            return False
    return True


def delete_registry_key(hive, subkey):
    try:
        with winreg.ConnectRegistry(None, hive) as reg:
            winreg.DeleteKey(reg, subkey)
        logging.info(f"Successfully deleted registry key: {subkey}")
    except FileNotFoundError:
        logging.error(f"Key not found: {subkey}")
    except PermissionError:
        logging.error(f"Permission denied: Unable to delete {subkey}. Ensure you have administrative privileges.")
    except Exception as e:
        logging.error(f"Failed to delete {subkey}: {e}")


def enumerate_directories():
    appdata_path = os.environ.get('APPDATA')
    program_files_path = os.environ.get('PROGRAMFILES')
    program_data_path = os.environ.get('PROGRAMDATA')

    paths = {
        appdata_path: [
            "LGHUB",
            "G HUB",
        ],
        program_files_path: [
            "LGHUB",
        ],
        program_data_path: [
            "Logishrd",
        ],
    }

    existing_directories = []

    for base_path, relative_paths in paths.items():
        if base_path:
            for rel_path in relative_paths:
                full_path = os.path.join(base_path, rel_path)
                if os.path.isdir(full_path):
                    existing_directories.append(full_path)

    return existing_directories


async def find_and_handle_prefetch():
    windows_prefetch_path = os.path.join(os.environ.get('WINDIR', ''), "Prefetch")
    prefetch_patterns = ["LGHUB*.pf", "GHUB*.pf"]

    all_prefetch_files = []
    for pattern in prefetch_patterns:
        full_pattern = os.path.join(windows_prefetch_path, pattern)
        prefetch_files = glob.glob(full_pattern)
        all_prefetch_files.extend(prefetch_files)

    async for pf_file in tqdm(all_prefetch_files, desc="Handling Prefetch Files", unit="File"):
        try:
            await aiofiles.os.remove(pf_file)
            logging.info(f"Deleted prefetch file: {pf_file}")
        except Exception as e:
            logging.error(f"Failed to delete prefetch file: {pf_file}. Error: {e}")


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_directory = "log"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")
    log_filepath = os.path.join(log_directory, log_filename)

    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s %(levelname)s %(reset)s %(message)s',
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

