import os
import datetime
import struct


def byteToBits(value, start_index, bit_cnt):
    return (value & (2 ** start_index - 1)) >> (start_index - bit_cnt)

def getDateTimeFromDosTime(dos_date, dos_time, dos_tenth_of_second):
    created_year = byteToBits(dos_date, 16, 7) + 1980
    created_month = byteToBits(dos_date, 9, 4)
    created_day = byteToBits(dos_date, 5, 5)
    created_hour = byteToBits(dos_time, 16, 5)
    created_minute = byteToBits(dos_time, 11, 6)
    created_second = int(byteToBits(dos_time, 5, 5) * 2 + dos_tenth_of_second / 100)
    creatied_milisecond = (dos_tenth_of_second % 100) * 10000
    return datetime.datetime(created_year, created_month, created_day, created_hour, created_minute, created_second, creatied_milisecond)

bytes_per_sector = 0
sectors_per_cluster = 0
reserved_sectors = 0
num_fats = 0
sectors_per_fat = 0
bytes_per_dir_entry = 32

def set_command_prompt(prompt):
    os.environ["PROMPT"] = prompt
    # os.system("cls")

def read_vbr(drive_path):
        try:
            with open(drive_path, 'rb') as f:
                # Read the VBR data
                boot_sector_data = f.read(512)
                
                return boot_sector_data

        except FileNotFoundError:
            print(f"Error: Drive identifier {drive_path} not found.")
        except PermissionError:
            print("Error: Permission denied. Run the script with appropriate privileges.")

def print_infor_dir(dir_entry):
        # Name and extension:
        # Attributes
        READ_ONLY = dir_entry[11] >> 0 & 1
        HIDDEN = dir_entry[11] >> 1 & 1
        SYSTEM = dir_entry[11] >> 2 & 1
        VOLUME = dir_entry[11] >> 3 & 1
        DIRECTORY = dir_entry[11] >> 4 & 1
        ARCHIVE = dir_entry[11] >> 5 & 1

        # TIME
        ## Created time
        created_tenth_of_second = int.from_bytes(dir_entry[13:14],'little')
        created_time = int.from_bytes(dir_entry[14:16], 'little')
        created_date = int.from_bytes(dir_entry[16:18], byteorder='little')
        if created_date !=0 and created_time!= 0 and created_tenth_of_second != 0:
            created_time = getDateTimeFromDosTime(created_date, created_time, created_tenth_of_second)

        ## Access time
        lastAccess = int.from_bytes(dir_entry[18:22], 'little')
        if lastAccess != 0:
            lastAccess = getDateTimeFromDosTime(lastAccess, 0, 0)

        ## Modified time
        modifiedTime = int.from_bytes(dir_entry[22:24], 'little')
        modifiedDate = int.from_bytes(dir_entry[24:26], 'little')
        if modifiedDate!=0 and modifiedTime!=0:
            modifiedDate = getDateTimeFromDosTime(modifiedDate, modifiedTime, 0)
        # Print the attributes
        print("*************************************************")
        print("Attributes:\t")
        print(f"\tREAD_ONLY: {READ_ONLY}")
        print(f"\tHIDDEN: {HIDDEN}")
        print(f"\tSYSTEM: {SYSTEM}")
        print(f"\tVOLUME: {VOLUME}")
        print(f"\tDIRECTORY: {DIRECTORY}")
        print(f"\tARCHIVE: {ARCHIVE}")
        print(f"Created Time: {created_time}")
        print(f"Last Access: {lastAccess}")
        print(f"Modified Date: {modifiedDate}")

def build_folder_tree(root_cluster, drive_path, flag):
    global bytes_per_sector
    global sectors_per_cluster
    global reserved_sectors
    global num_fats
    global sectors_per_fat
    global bytes_per_dir_entry
    global detail 
    root_dir_offset = (reserved_sectors + num_fats * sectors_per_fat + (root_cluster - 2) * sectors_per_cluster) * bytes_per_sector
    folder_dict = {}
    def read_sub_entry(entry):
        name = ""
        for i in range(1, 31):
            byte = entry[i]
            if byte != 0x00 and byte != 0xFF and i not in [11, 12, 13, 26, 27]:
                if byte == 0x2E:
                    name += "."
                else:
                    name += chr(byte)
        return name
    
    

    if flag == 1:
        with open(drive_path, 'rb') as f1:
            f1.seek(root_dir_offset)
            sector1 = f1.read(32)
            print(sector1)
            print_infor_dir(sector1)
    with open(drive_path, 'rb') as f:
        f.seek(root_dir_offset)
        main_entry_name = ""
        sub_entry_name = ""
        while True:
            sector = f.read(512)
            for i in range(0, bytes_per_sector, bytes_per_dir_entry):
                dir_entry = sector[i:i + bytes_per_dir_entry]
                if not dir_entry[0]:  # End of the directory
                    return folder_dict

                if dir_entry[0] != 0xE5:
                    if dir_entry[11] == 0x08:  # Volume label
                        volume_label = bytes(dir_entry[:11]).decode(errors='ignore').strip()
                        main_entry_name = ""

                    elif dir_entry[11] == 0x0F:  # Subdirectory or file entry
                        sub_entry_order = dir_entry[0]
                        if sub_entry_order == 0x01 or sub_entry_order == 0x41:  # First or only sub entry
                            sub_entry_name = read_sub_entry(dir_entry)
                            main_entry_name = sub_entry_name + main_entry_name
                            sub_entry_name = ""
                        else:
                            sub_entry_name = read_sub_entry(dir_entry)
                            main_entry_name = sub_entry_name + main_entry_name
                            sub_entry_name = main_entry_name

                    elif dir_entry[11] == 0x10:  # Folder entry
                        if len(main_entry_name) > 0:
                            folder_dict[main_entry_name] = int.from_bytes(dir_entry[26:27])
                            main_entry_name = ""
                        else:
                            folder_name = bytes(dir_entry[:11]).decode(errors='ignore').strip()
                            folder_dict[folder_name] = int.from_bytes(dir_entry[26:27])

                    elif dir_entry[11] == 0x20:  # File entry
                        if len(main_entry_name) > 0:
                            folder_dict[main_entry_name] = int.from_bytes(dir_entry[26:27])
                            main_entry_name = ""
                        else:
                            file_name = bytes(dir_entry[:8]).decode(errors='ignore').strip()
                            extension = bytes(dir_entry[8:11]).decode(errors='ignore').strip()
                            if file_name != '':  # Skip empty file entries
                                file_name_with_extension = f"{file_name}.{extension}"
                                folder_dict[file_name_with_extension] = int.from_bytes(dir_entry[26:27])
                                if flag == 2:
                                    print_infor_dir(dir_entry)
                                    print("********************* DATA *********************")
                                    numbytes = int.from_bytes(dir_entry[20:22])
                                    root_dir_offset = (reserved_sectors + num_fats * sectors_per_fat + (root_cluster - 2) * sectors_per_cluster) * bytes_per_sector
                                    print(root_dir_offset)
                                    print(numbytes)
                                else:
                                    continue

                    elif dir_entry[11] == 0x16:  # System File
                        if len(main_entry_name) > 0:
                            main_entry_name = ""
                        else:
                            file_name = bytes(dir_entry[:11]).decode(errors='ignore').strip()
               

                
def loop(name, root_cluster, drive_path):
    new_prompt = f"{name}:> "
    set_command_prompt(new_prompt)
    folder_dict = build_folder_tree(root_cluster, drive_path, 0)
    while True:
        command = input(new_prompt)
        for key in folder_dict.keys():
            print(key)
        print()
        if command.lower() == "exit":
            break
        if command.lower() == "info":
            print(f"Bytes per sector: {bytes_per_sector}")
            print(f"Sectors per cluster: {sectors_per_cluster}")
            print(f"Reserved: {reserved_sectors}")
            print(f"Numbers of FATs: {num_fats}")
            print(f"Sectors per FAT: {sectors_per_fat}")
            print(f"Root cluster: {root_cluster}")
            folder_dict = build_folder_tree(root_cluster, drive_path, 1)
        
        if command.lower() == "ls":
            for key in folder_dict.keys():
                print(key)
            print()

        if command in folder_dict:
            print()
            loop(command, folder_dict[command], drive_path)



def start_program():
    name = input("Enter the name: ")
    drive_path = f"\\\\.\\{name}:"
    sector = read_vbr(drive_path)

    global bytes_per_sector
    global sectors_per_cluster
    global reserved_sectors
    global num_fats
    global sectors_per_fat
    global bytes_per_dir_entry
    
    bytes_per_sector = int.from_bytes(sector[11:13], 'little')
    sectors_per_cluster = int.from_bytes(sector[13:14], "little")
    reserved_sectors = int.from_bytes(sector[14:16], "little")
    num_fats = int.from_bytes(sector[16:17], "little")
    sectors_per_fat = int.from_bytes(sector[36:40], "little")
    root_cluster = int.from_bytes(sector[44:48], "little")

    new_prompt = f"{name}:> "
    set_command_prompt(new_prompt)
    checkFile = 0
    folder_dict = build_folder_tree(root_cluster, drive_path, 0)
    
    while True:
        command = input(new_prompt)
        if command.lower() == "info":
            print(f"Bytes per sector: {bytes_per_sector}")
            print(f"Sectors per cluster: {sectors_per_cluster}")
            print(f"Reserved: {reserved_sectors}")
            print(f"Numbers of FATs: {num_fats}")
            print(f"Sectors per FAT: {sectors_per_fat}")
            print(f"Root cluster: {root_cluster}")
            build_folder_tree(root_cluster, drive_path, 1)
            
        if command.lower() == "exit":
            break

        if command.lower() == "ls":
            for key in folder_dict.keys():
                print(key)
            print()

        if command in folder_dict:
            print()
            if command.find("TXT") >= 0:
                build_folder_tree(root_cluster, drive_path, 2)
            else:
                loop(command, folder_dict[command], drive_path)

        

start_program()