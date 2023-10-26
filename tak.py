import ctypes
import os


def print_func(sector):
    for byte in sector:
        print(f"{byte:02X}", end=" ")


def read_sector(drive, read_point):
    ret_code = 0
    bytes_read = ctypes.c_ulong()
    sector = (ctypes.c_ubyte * 512)()

    device = ctypes.windll.kernel32.CreateFileW(
        drive,                               # Drive to open
        ctypes.c_uint32(0x80000000),         # GENERIC_READ
        # FILE_SHARE_READ | FILE_SHARE_WRITE
        ctypes.c_uint32(0x00000001),
        None,                                # Security Descriptor
        ctypes.c_uint32(0x00000003),         # OPEN_EXISTING
        ctypes.c_uint32(0),                  # File attributes
        None                                # Handle to template
    )

    if device == -1:  # Open Error
        print(f"CreateFile: {ctypes.windll.kernel32.GetLastError()}")
        return 1

    ctypes.windll.kernel32.SetFilePointer(
        device, read_point, None, 0)  # Set a Point to Read

    if not ctypes.windll.kernel32.ReadFile(
        device,
        sector,
        512,
        ctypes.byref(bytes_read),
        None
    ):
        print(f"ReadFile: {ctypes.windll.kernel32.GetLastError()}")
    else:
        print("Success!")
        # print_func(sector)
        ctypes.windll.kernel32.CloseHandle(device)

    return sector


def build_folder_tree(drive):
    sector = read_sector(drive, 0)
    if sector is None:
        return

    bytes_per_sector = int.from_bytes(sector[11:13], 'little')
    sectors_per_cluster = int.from_bytes(sector[13:14], "little")
    reserved_sectors = int.from_bytes(sector[14:16], "little")
    num_fats = int.from_bytes(sector[16:17], "little")
    sectors_per_fat = int.from_bytes(sector[36:40], "little")
    root_cluster = int.from_bytes(sector[44:48], "little")

    bytes_per_dir_entry = 32

    root_dir_offset = (reserved_sectors + num_fats *
                       sectors_per_fat) * bytes_per_sector

    device = ctypes.windll.kernel32.CreateFileW(drive,  # Drive to open
                                                # GENERIC_READ
                                                ctypes.c_uint32(0x80000000),
                                                # FILE_SHARE_READ | FILE_SHARE_WRITE
                                                ctypes.c_uint32(0x00000001),
                                                None,  # Security Descriptor
                                                # OPEN_EXISTING
                                                ctypes.c_uint32(0x00000003),
                                                # File attributes
                                                ctypes.c_uint32(0),
                                                None  # Handle to template
                                                )
    if device == -1:  # Open Error
        print(f"CreateFile: {ctypes.windll.kernel32.GetLastError()}")
        return

    ctypes.windll.kernel32.SetFilePointer(
        device, root_dir_offset, None, 0)  # Set a Point to Read

    while True:
        sector = (ctypes.c_ubyte * bytes_per_sector)()
        bytes_read = ctypes.c_ulong()
        if not ctypes.windll.kernel32.ReadFile(device, sector, bytes_per_sector, ctypes.byref(bytes_read), None):
            print(f"ReadFile: {ctypes.windll.kernel32.GetLastError()}")
            break

        for i in range(0, bytes_per_sector, bytes_per_dir_entry):
            dir_entry = sector[i:i+bytes_per_dir_entry]
            if not dir_entry[0]:  # End of the directory
                ctypes.windll.kernel32.CloseHandle(device)
                print("Folder tree created successfully.")
                return

            if dir_entry[0] != 0xE5: # Long file name entry
                if dir_entry[11] == 0x0F:  
                    continue

                if dir_entry[11] == 0x10:  # Subdirectory entry
                    folder_name = bytes(dir_entry[:8]).decode(
                        errors='ignore').strip()
                    if folder_name != '.' and folder_name != '..' and folder_name != "":
                        subfolder_path = f"{drive}\{folder_name}"
                        print(f"Folder: {folder_name}")
                            
        #                    os.makedirs(subfolder_path, exist_ok=True)
                else:  # File entry
                    file_name = bytes(dir_entry[:8]).decode(
                        errors='ignore').strip()
                    extension = bytes(dir_entry[8:11]).decode(
                        errors='ignore').strip()
                    if file_name != '':  # Skip empty file entries
                        file_name_with_extension = f"{file_name}.{extension}"
                        print(f"File: {file_name_with_extension}")

    ctypes.windll.kernel32.CloseHandle(device)
    print("Error: Failed to build folder tree.")


drive = "\\\\.\\D:"
build_folder_tree(drive)