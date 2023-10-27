import os

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

def read_file(file_path):

    try:
        with open(file_path, 'rb') as f:
            boot_sector_data = f.read(512)
            return boot_sector_data

    except FileNotFoundError:
        print(f"Error: Drive identifier {file_path} not found.")
    except PermissionError:
        print("Error: Permission denied. Run the script with appropriate privileges.")


def build_folder_tree(root_cluster, drive_path):

    global bytes_per_sector
    global sectors_per_cluster
    global reserved_sectors
    global num_fats
    global sectors_per_fat
    global bytes_per_dir_entry

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
                            folder_name = bytes(dir_entry[:8]).decode(errors='ignore').strip()
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

                    elif dir_entry[11] == 0x16:  # System File
                        if len(main_entry_name) > 0:
                            main_entry_name = ""
                        else:
                            file_name = bytes(dir_entry[:11]).decode(errors='ignore').strip()

def loop(name, root_cluster, drive_path):
    new_prompt = f"{name}:> "
    set_command_prompt(new_prompt)
    folder_dict = build_folder_tree(root_cluster, drive_path)

    while True:
        command = input(new_prompt)
        if command.lower() == "exit":
            break

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

    folder_dict = build_folder_tree(root_cluster, drive_path)

    while True:
        command = input(new_prompt)
        if command.lower() == "Info":
            print(f"Bytes per sector: {bytes_per_sector}")
            print(f"Sectors per cluster: {sectors_per_cluster}")
            print(f"Reserved: {reserved_sectors}")
            print(f"Numbers of FATs: {num_fats}")
            print(f"Sectors per FAT: {sectors_per_fat}")
            print(f"Root cluster: {root_cluster}")

        if command.lower() == "exit":
            break

        if command.lower() == "ls":
            for key in folder_dict.keys():
                print(key)
            print()

        if command in folder_dict:
            print()
            loop(command, folder_dict[command], drive_path)

start_program()