import os
import datetime
import struct

firstAttr = {
    1: 'D',
    2: 'A'
}

secondAttr = {
    1: 'R',
    2: 'H',
    3: 'RH',
    4: 'S',
    6: 'HS',
    8: 'V'
}

app = {
    ".mp4": "Windows Media Player",
    ".mp3": "Windows Media Player"
    "."
}

# Define column widths
name_width = 25
size_width = 20
attribute_width = 25
sector_width = 20


def byteToBits(value, start_index, bit_cnt):
    return (value & (2 ** start_index - 1)) >> (start_index - bit_cnt)


def getDateTimeFromDosTime(dos_date, dos_time, dos_tenth_of_second):
    created_year = byteToBits(dos_date, 16, 7) + 1980
    created_month = byteToBits(dos_date, 9, 4)
    created_day = byteToBits(dos_date, 5, 5)
    created_hour = byteToBits(dos_time, 16, 5)
    created_minute = byteToBits(dos_time, 11, 6)
    created_second = int(byteToBits(dos_time, 5, 5) *
                         2 + dos_tenth_of_second / 100)
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
    # Created time
    created_tenth_of_second = int.from_bytes(dir_entry[13:14], 'little')
    created_time = int.from_bytes(dir_entry[14:16], 'little')
    created_date = int.from_bytes(dir_entry[16:18], byteorder='little')
    if created_date != 0 and created_time != 0 and created_tenth_of_second != 0:
        created_time = getDateTimeFromDosTime(
            created_date, created_time, created_tenth_of_second)

    # Access time
    lastAccess = int.from_bytes(dir_entry[18:22], 'little')
    if lastAccess != 0:
        lastAccess = getDateTimeFromDosTime(lastAccess, 0, 0)

    # Modified time
    modifiedTime = int.from_bytes(dir_entry[22:24], 'little')
    modifiedDate = int.from_bytes(dir_entry[24:26], 'little')
    if modifiedDate != 0 and modifiedTime != 0:
        modifiedDate = getDateTimeFromDosTime(modifiedDate, modifiedTime, 0)
    # Print the attributes
    print("***********************************************")
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


def print_the_header_row(root_cluster, drive_path):
    root_dir_offset = find_root_dir_offset(root_cluster)
    with open(drive_path, 'rb') as f1:
        f1.seek(root_dir_offset)
        sector1 = f1.read(32)
        print_infor_dir(sector1)


def find_root_dir_offset(root_cluster):
    global bytes_per_sector
    global sectors_per_cluster
    global reserved_sectors
    global num_fats
    global sectors_per_fat
    global bytes_per_dir_entry
    root_dir_offset = (reserved_sectors + num_fats * sectors_per_fat +
                       (root_cluster - 2) * sectors_per_cluster) * bytes_per_sector
    return root_dir_offset


def print_txt_File(root_cluster, drive_path, size):
    root_dir_offset = find_root_dir_offset(root_cluster)
    with open(drive_path, 'rb') as f:
        f.seek(root_dir_offset)
        data = f.read(size)
        print("Content in the file: ")
        print(bytes(data).decode(errors='ignore'))


def build_folder_tree(root_cluster, drive_path):
    root_dir_offset = find_root_dir_offset(root_cluster)
    folder_dict = {}

    def read_sub_entry(entry):
        name = entry[1:11].decode(encoding='utf-16', errors='ignore')
        name += entry[14:26].decode(encoding='utf-16', errors='ignore')
        name += entry[28:32].decode(encoding='utf-16', errors='ignore')
        name = name.replace('￿', '')
        return name

    with open(drive_path, 'rb') as f:
        f.seek(root_dir_offset)
        main_entry_name = ""
        sub_entry_name = ""
        while True:
            sector = f.read(512)
            for i in range(0, bytes_per_sector, bytes_per_dir_entry):
                dir_entry = sector[i:i + bytes_per_dir_entry]
                size = int.from_bytes(dir_entry[28:32], 'little')
                sectorID = i * bytes_per_sector

                if not dir_entry[0]:  # End of the directory
                    return folder_dict

                if dir_entry[0] not in [0xE5, 0x2E]:
                    if dir_entry[11] == 0x0F:  # Sub Entry
                        sub_entry_order = dir_entry[0]
                        sub_entry_name = read_sub_entry(dir_entry)
                        main_entry_name = sub_entry_name + main_entry_name
                        sub_entry_name = "" if sub_entry_order in [
                            0x01, 0x41] else main_entry_name
                    else:
                        attribute = ''
                        if dir_entry[11] % 16 != 0:
                            attribute = secondAttr[dir_entry[11] % 16]
                        if (dir_entry[11] // 16) % 16 != 0:
                            attribute += firstAttr[(dir_entry[11] // 16) % 16]

                        if len(main_entry_name) > 0:
                            main_entry_name = main_entry_name[:len(
                                main_entry_name) - 1]
                            root_cluster = int.from_bytes(
                                dir_entry[26:27], 'little')

                            folder_dict[main_entry_name] = {
                                "firstCluster": root_cluster,
                                "size": size,
                                "attribute": attribute,
                                "sector": sectorID
                            }
                            main_entry_name = ""
                        else:
                            file_name = dir_entry[:8].decode(
                                'utf-8', errors="ignore").strip()
                            extension = bytes(dir_entry[8:11]).decode(
                                errors="ignore").strip()
                            root_cluster = int.from_bytes(
                                dir_entry[26:27], 'little')

                            file_name_with_extension = f"{file_name}{extension}" if extension and attribute[len(
                                attribute) - 1] != 'A' else f"{file_name}.{extension}" if extension else f"{file_name}"

                            folder_dict[file_name_with_extension] = {
                                "firstCluster": root_cluster,
                                "size": size,
                                "attribute": attribute,
                                "sector": sectorID
                            }


def loop(name, root_cluster, drive_path):
    new_prompt = f"{name}:> "
    set_command_prompt(new_prompt)
    header = f"\t{'NAME':<{name_width}} {'SIZE':<{size_width}} {'ATTRIBUTE':<{attribute_width}} SECTOR"
    folder_dict = build_folder_tree(root_cluster, drive_path)
    while True:
        command = input(new_prompt)
        if command.lower() == "exit":
            break
        if command.lower() == "info":
            print(f"-----------------    INFORMATION    ----------------------")
            print(f"Bytes per sector: {bytes_per_sector}")
            print(f"Sectors per cluster: {sectors_per_cluster}")
            print(f"Reserved: {reserved_sectors}")
            print(f"Numbers of FATs: {num_fats}")
            print(f"Sectors per FAT: {sectors_per_fat}")
            print(f"Root cluster: {root_cluster}")
            print_the_header_row(root_cluster, drive_path)
        if command.lower() == "list":
            print(header)
            for key in folder_dict:
                sz = folder_dict[key]["size"]
                attr = folder_dict[key]["attribute"]
                st = folder_dict[key]["sector"]
                line = f"\t{key:<{name_width}} {sz:<{size_width}} {attr:<{attribute_width}}{st:<{sector_width}}"
                print(line)

        if command in folder_dict:
            if (command.endswith(".TXT") or command.endswith(".txt")) and folder_dict[command]["attribute"].endswith("A"):
                print_txt_File(
                    folder_dict[command]["firstCluster"], drive_path, folder_dict[command]["size"])
            elif folder_dict[command]["attribute"].endswith("D"):
                loop(command, folder_dict[command]["firstCluster"], drive_path)
            else:
                print("\fDùng phần mềm tương thích please.")


def start_program():
    name = input("Enter disk: ")
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

    header = f"\t{'NAME':<{name_width}} {'SIZE':<{size_width}} {'ATTRIBUTE':<{attribute_width}} SECTOR"
    folder_dict = build_folder_tree(root_cluster, drive_path)

    while True:
        command = input(new_prompt)
        if command.lower() == "info":
            print(f"-----------------    INFORMATION    ----------------------")
            print(f"Bytes per sector: {bytes_per_sector}")
            print(f"Sectors per cluster: {sectors_per_cluster}")
            print(f"Reserved: {reserved_sectors}")
            print(f"Numbers of FATs: {num_fats}")
            print(f"Sectors per FAT: {sectors_per_fat}")
            print(f"Root cluster: {root_cluster}")
            print_the_header_row(root_cluster, drive_path)
        if command.lower() == "list":
            print(header)
            for key in folder_dict:
                sz = folder_dict[key]["size"]
                attr = folder_dict[key]["attribute"]
                st = folder_dict[key]["sector"]
                line = f"\t{key:<{name_width}} {sz:<{size_width}} {attr:<{attribute_width}}{st:<{sector_width}}"
                print(line)

        if command in folder_dict:
            if (command.endswith(".TXT") or command.endswith(".txt")) and folder_dict[command]["attribute"].endswith("A"):
                print_txt_File(
                    folder_dict[command]["firstCluster"], drive_path, folder_dict[command]["size"])
            elif folder_dict[command]["attribute"].endswith("D"):
                loop(command, folder_dict[command]["firstCluster"], drive_path)
            else:
                print("\fDùng phần mềm tương thích please.")

        if command.lower() == "exit":
            break


start_program()
