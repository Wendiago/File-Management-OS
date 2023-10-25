import os

# Initialize global variables
byte_per_sector = None
mft_cluster = None
sector_per_cluster = None

# def read_MBR(drive_id):
#     try:
#         path = r"\\.\PHYSICALDRIVE" + drive_id

#         with open(path, 'rb') as f:
#             mbr_data = f.read(512)  # Read the first 512 bytes (MBR size)

#         if len(mbr_data) != 512:
#             print("Error: MBR size is not 512 bytes.")
#         else:
#             # Extract partition information
#             partition_start_offset = 446  # MBR partition table starts at byte 446
#             partition_entry_size = 16  # Size of each partition entry

#             # Read the partition entry for the first partition
#             partition_entry = mbr_data[partition_start_offset:partition_start_offset + partition_entry_size]

#             # Extract the starting sector number of the first partition
#             partition_start_sector = partition_entry[8:12]
#             first_sector_number = int.from_bytes(partition_start_sector, byteorder='little')

#             # Print the MBR in hexadecimal format
#             mbr_hex = ' '.join(['{:02X}'.format(byte) for byte in mbr_data])
#             #print("MASTER BOOT RECORD: ", mbr_hex)
            
#             # Print the first partition's partition entry in hexadecimal format
#             partition_entry_hex = ' '.join(['{:02X}'.format(byte) for byte in partition_entry])
#             #print("PARTITION 1: ", partition_entry_hex)
            
#             return first_sector_number

#     except FileNotFoundError:
#         print(f"Error: Drive identifier PHYSICALDRIVE{drive_id} not found.")
#     except PermissionError:
#         print("Error: Permission denied. Run the script with appropriate privileges.")

def print_VBR_info(vbr_data):
    global mft_cluster, sector_per_cluster, byte_per_sector
    # Function to print VBR information, including BPB details
    if vbr_data is None:
        print("Error: VBR data is None.")
        return

    print("\t================VBR information==================")
    # Print the JMP instruction and OEM ID
    print("JMP Instruction:", ' '.join(['{:02X}'.format(byte) for byte in vbr_data[0:3]]))
    print("OEM ID:", vbr_data[3:11].decode('utf-8'))
    
    # BPB (BIOS Parameter Block) starts at offset 11 in the VBR
    bpb_data = vbr_data[11:84]
    
    # BPB details
    print("\n\tBIOS Parameter Block (BPB) Details:")
    print("Bytes Per Sector: ", int.from_bytes(bpb_data[0:2], byteorder='little'))
    print("Sectors Per Cluster: ", int.from_bytes(bpb_data[2:3], byteorder='little'))
    print("Reserved sector: ", int.from_bytes(bpb_data[3:5], byteorder='little'))
    print("Media Type: ", int.from_bytes(bpb_data[10:11], byteorder='little'))
    print("Sectors per track: ", int.from_bytes(bpb_data[13:15], byteorder='little'))
    print("Number of heads: ", int.from_bytes(bpb_data[15:17], byteorder='little'))
    print("First sector of disk: ", int.from_bytes(bpb_data[17:21], byteorder='little'))
    print("Total sector: ", int.from_bytes(bpb_data[29:37], byteorder='little'))
    print("MFT cluster number: ", int.from_bytes(bpb_data[37:45], byteorder='little'))
    print("MFT Mirror cluster number: ", int.from_bytes(bpb_data[45:53], byteorder='little'))
    print("Clusters Per File Record Segment: ", int.from_bytes(bpb_data[53:57], byteorder='little'))
    print("Clusters Per Index Buffer: ", int.from_bytes(bpb_data[57:61], byteorder='little'))
    print("Volume Serial Number: ", int.from_bytes(bpb_data[61:69], byteorder='little'))
    print("Checksum: ", int.from_bytes(bpb_data[69:73], byteorder='little'))
    
    #Get mft cluster number
    mft_cluster = int.from_bytes(bpb_data[37:45], byteorder='little')
    #Get sector per cluster
    sector_per_cluster = int.from_bytes(bpb_data[2:3], byteorder='little')
    #Byte per sector
    byte_per_sector = int.from_bytes(bpb_data[0:2], byteorder='little')

    #reading MFT
        
def read_vbr(disk_letter):
    try:
        disk_path = fr'\\.\{disk_letter}:'

        with open(disk_path, 'rb') as f:
            # Read the VBR data
            vbr_data = f.read(512)
            
            return vbr_data

    except FileNotFoundError:
        print(f"Error: Drive identifier {disk_letter} not found.")
    except PermissionError:
        print("Error: Permission denied. Run the script with appropriate privileges.")

def detect_filesystem_using_vbr(vbr_data):
    try:
        # Check for FAT12, FAT16, or FAT32
        if vbr_data[0x36:0x3A] == b'FAT ':
            return 'FAT' + str(vbr_data[0x52])

        # Check for NTFS
        if vbr_data[3:11] == b'NTFS    ':
            return 'NTFS'

        return 'Unknown'
    except Exception as e:
        return 'Error'
    
def get_MFT(disk_letter, next_sector):
    try:
        global mft_cluster, sector_per_cluster, byte_per_sector
        cluster_number = mft_cluster * sector_per_cluster + next_sector
        disk_path = fr'\\.\{disk_letter}:'
        
        with open(disk_path, 'rb') as f:
            f.seek(cluster_number * byte_per_sector)
            mft_data = f.read(1024)
            # mft_data_hex = ' '.join(['{:02X}'.format(byte) for byte in mft_data])
            # print('MFT Data: ', mft_data_hex)
            return mft_data
    except FileNotFoundError:
        print('Error: File not found.')
    except PermissionError:
        print('Error: Permission denied. Run the script with appropriate privileges.')
    except Exception as e:
        print(f'Error reading MFT: {str(e)}')

def check_MFT(mft_data):
    if mft_data is None:
        return False

    # Check if the first 4 bytes contain "FILE" to ensure it's an MFT entry for a file
    if mft_data[:4] != b'FILE':
        return False
    
    return True

def MFT_info(mft_data):
    # Extract and print the sequence number (2 bytes) at offset 10
    sequence_number = int.from_bytes(mft_data[0x10:0x12], byteorder='little')

    # Extract and print the flags (2 bytes) at offset 16
    flags = int.from_bytes(mft_data[0x16:0x18], byteorder='little')
    used = flags & 0x0001

    # Extract and print file permission (4 bytes) at offset 70
    file_permission = int.from_bytes(mft_data[0x70:0x74], byteorder='little')
    system_file = (file_permission>>1 & 0x1)

    if (used == False or system_file == True):
        return None

    # Extract and print the ID (4 bytes) at offset 0x2C
    mft_entry_id = int.from_bytes(mft_data[0x2C:0x30], byteorder='little')

    # Extract and print the parent ID (6 bytes) at offset 0xB0
    parent_id = int.from_bytes(mft_data[0xB0:0xB6], byteorder='little')

    # Extract and print the parent sequence number (2 bytes) at offset 0xB6
    parent_sequence = int.from_bytes(mft_data[0xB6:0xB8], byteorder='little')

    # Extract and print the name length (1 byte) at offset 0xF0
    name_length = int.from_bytes(mft_data[0xF0:0xF1], byteorder='little')

    # Extract and print the name (variable length) at offset 0xF2
    name_start = 0xF2
    name_end = name_start + name_length*2
    name = mft_data[name_start:name_end].decode('utf-16le')

    return TreeNode(mft_entry_id, sequence_number, parent_id, parent_sequence, name)
    
#============================Tree==================================
class TreeNode:
    def __init__(self, id, sequence, parent_id, parent_sequence, name):
        self.id = id
        self.sequence = sequence
        self.parent_id = parent_id
        self.parent_sequence = parent_sequence
        self.name = name
        self.children = []

def add_child_by_parent_id_and_sequence(root, child):
    parent = find_node(root, child.parent_id, child.parent_sequence)
    if parent:
        parent.children.append(child)

def find_node(node, parent_id, parent_sequence):
    if node:
        if node.id == parent_id and node.sequence == parent_sequence:
            return node
        for child in node.children:
            result = find_node(child, parent_id, parent_sequence)
            if result:
                return result
    return None

def build_tree(id, sequence, parent_id, parent_sequence, name):
    root = TreeNode(id, sequence, parent_id, parent_sequence, name)
    i = 27
    while True:
        mft_data = get_MFT(disk_letter, 2*i)
        i = i + 1
        if (check_MFT(mft_data) == True):
            nodeTree = MFT_info(mft_data)
            if (nodeTree):
                add_child_by_parent_id_and_sequence(root, nodeTree)
        else:
            break
    return root

def print_tree(node, depth=0, indent=''):
    if node:
        new_indent = indent + '|   ' if depth > 1 else ''
        print(f"{new_indent}{'|---' if depth > 0 else ''}{node.name}")
        for child in node.children:
            print_tree(child, depth + 1, new_indent)


#============================Main==================================
disk_letter = "D"
#Read VBR Data from disk
vbr_data = read_vbr(disk_letter)
#Detect file system
fileSystemType = detect_filesystem_using_vbr(vbr_data)
if (fileSystemType == 'NTFS'):
    print_VBR_info(vbr_data)
    #Read MFT Data
    
else:
    print("\nNot NTFS")

print("")

# Build the tree
root_node = build_tree(5, 5, 0, 0, '.')

# Print the tree
print_tree(root_node)