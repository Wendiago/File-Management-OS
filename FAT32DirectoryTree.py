import os

BYTE_P_SECTOR = 512

def read_vbr(drive_path):
    try:
        with open(drive_path, 'rb') as f:
            # Read the VBR data
            boot_sector_data = f.read(BYTE_P_SECTOR)
            
            return boot_sector_data

    except FileNotFoundError:
        print(f"Error: Drive identifier {drive_path} not found.")
    except PermissionError:
        print("Error: Permission denied. Run the script with appropriate privileges.")    
def read_folder(path):
    try:
        dirs = os.listdir( path )
        for file in dirs:

            with open(path + '/' + file ,'rb') as f:
                boot_sector_data = f.read(BYTE_P_SECTOR)
                print("open " + file)
    except FileNotFoundError:
        print(f"Error: Drive identifier {drive_path} not found.")
    except PermissionError:
        print("Error: Permission denied. Run the script with appropriate privileges.")
######################################## MAIN  
def build_folder_tree(drive_path):
    # PRINT 
    boot_sector_data = read_vbr(drive_path)
    bytes_per_sector = int.from_bytes(boot_sector_data[11:13], "little")
    reserved_sectors = int.from_bytes(boot_sector_data[14:16], "little")
    num_fats = int.from_bytes(boot_sector_data[16:17], "little")
    sectors_per_fat = int.from_bytes(boot_sector_data[36:40], "little")
    bytes_per_dir_entry = 32

    root_dir_offset = (reserved_sectors + num_fats *
                        sectors_per_fat) * bytes_per_sector
    
    
    print(f"drivepath: {drive_path} ")

    with open(drive_path, 'rb') as f:
        # Read the VBR data
        f.seek(root_dir_offset)
        while True:
            sector = f.read(512)
            for i in range(0, bytes_per_sector, bytes_per_dir_entry):
                dir_entry = sector[i:i+bytes_per_dir_entry]
                if not dir_entry[0]:  # End of the directory
                    print("Folder tree created successfully.")
                    return

                if dir_entry[0] != 0xE5: # Long file name entry
                    if dir_entry[11] == 0x0F:  
                        continue

                    if dir_entry[11] == 0x10:  # Subdirectory entry
                        folder_name = bytes(dir_entry[:8]).decode(
                            errors='ignore').strip()
                        if folder_name != '.' and folder_name != '..' and folder_name != "":
                            subfolder_path = fr"{drive_path}\{folder_name}"
                            print(f"Folder: {folder_name}")
                            read_folder(subfolder_path)
                           
                    else:  # File entry
                        file_name = bytes(dir_entry[:8]).decode(
                            errors='ignore').strip()
                        extension = bytes(dir_entry[8:11]).decode(
                            errors='ignore').strip()
                        if file_name != '':  # Skip empty file entries
                            file_name_with_extension = f"{file_name}.{extension}"
                            print(f"File: {file_name_with_extension}")


##################### MAIN #########################
drive_letter = "D"
drive_path = fr'{drive_letter}:'
#build_folder_tree(drive_path)
read_folder(fr'D:/')