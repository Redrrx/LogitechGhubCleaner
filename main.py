import asyncio
import glob
import logging
import os
from winreg import HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE
import aiofiles.os
import aioshutil
from tqdm.asyncio import tqdm, trange
from ToolBox import delete_registry_key, unlock_file, find_and_handle_prefetch, enumerate_directories, is_admin, \
    setup_logging
from colorama import Back, Style, Fore

setup_logging()

ascii_art = f"""{Fore.LIGHTBLUE_EX}
   _____   _    _ _    _ ____     _____ _                              
  / ____| | |  | | |  | |  _ \   / ____| |                             
 | |  __  | |__| | |  | | |_) | | |    | | ___  __ _ _ __  _   _ _ __  
 | | |_ | |  __  | |  | |  _ <  | |    | |/ _ \/ _` | '_ \| | | | '_ \ 
 | |__| | | |  | | |__| | |_) | | |____| |  __/ (_| | | | | |_| | |_) |
  \_____| |_|  |_|\____/|____/   \_____|_|\___|\__,_|_| |_|\__,_| .__/ 
                                                                | |    
                                                                |_|
"""

info_text = f"""{Fore.RESET}
* This piece of code was made to clean up Broken G HUB installs.
* After Logitech changes, this tool might not be needed anymore unless your install is old.
* Close Logitech G HUB before commencing operations. Expect explorer to possibly crash as file unlock is done.
"""


async def main():
    if not await is_admin():
        logging.error(
            "Due the nature of the unlocking mechanism and the registery changes to be done,this script requires administrative privileges to run.")
        input()
        return
    print(ascii_art)
    print(info_text)
    print("Press any key to start...")
    input()
    directories = enumerate_directories()
    all_files = []
    unique_files = set()

    for directory in directories:
        logging.info(f"Accumulating files in directory: {directory}")
        files_in_dir = glob.glob(os.path.join(directory, '**'), recursive=True)
        for file in files_in_dir:
            if os.path.isfile(file) and file not in unique_files:
                unique_files.add(file)
                all_files.append(file)

    tasks = []
    for file_path in all_files:
        async def unlock_and_delete(file_path=file_path):
            if await unlock_file(file_path, forced=True):
                try:
                    await aiofiles.os.remove(file_path)
                    logging.info(f"Successfully deleted {file_path}")
                except PermissionError as e:
                    logging.error(f"PermissionError: {e}. Could not delete {file_path}")
                except Exception as e:
                    logging.error(f"Failed to delete {file_path}. Error: {e}")

        tasks.append(unlock_and_delete())

    for directory in set(directories):
        async def delete_dir(directory=directory):
            await aioshutil.rmtree(directory, ignore_errors=True)
            logging.info(f"Deleted directory: {directory}")

        tasks.append(delete_dir())

    with tqdm(total=len(tasks), desc="Processing files and directories") as pbar:
        await asyncio.gather(*[asyncio.ensure_future(task) for task in tasks])
    await find_and_handle_prefetch()

    keys_to_delete = [
        (HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\CTF\Compatibility\lghub.exe"),
        (HKEY_CURRENT_USER, r"Software\Classes\AppID\lghub.exe"),
        (HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\lghub.exe")
    ]

    for hive, subkey in keys_to_delete:
        delete_registry_key(hive, subkey)

    logging.info("Operation completed feel free to read up on the logs, press any key to quit.")
    input()



if __name__ == "__main__":
    asyncio.run(main())
