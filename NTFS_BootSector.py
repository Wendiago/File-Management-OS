import os
import re

# Initialize global variables
byte_per_sector = None
mft_cluster = None
sector_per_cluster = None

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
            f.close()
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
    
def get_MFT(disk_letter, next_id):
    try:
        global mft_cluster, sector_per_cluster, byte_per_sector
        offset = mft_cluster * sector_per_cluster * byte_per_sector + next_id * 1024
        disk_path = fr'\\.\{disk_letter}:'
        
        with open(disk_path, 'rb') as f:
            f.seek(offset, 0)
            mft_data = f.read(1024)
            # mft_data_hex = ' '.join(['{:02X}'.format(byte) for byte in mft_data])
            # print('MFT Data: ', mft_data_hex)
            f.close()
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

def MFT_info(mft_data, disk_letter):
    # Extract the sequence number (2 bytes) at offset 10
    sequence_number = int.from_bytes(mft_data[0x10:0x12], byteorder='little')

    # location and length of the standard_information attribute
    offset_standard_information = int.from_bytes(mft_data[0x14:0x16], byteorder='little')
    type_standard_information = int.from_bytes(mft_data[offset_standard_information:offset_standard_information + 4], byteorder='little')
    length_standard_information = int.from_bytes(mft_data[offset_standard_information + 4:offset_standard_information + 8], byteorder='little')

    if (type_standard_information != 16):
        return None
    
    # location and length of the file_name attribute
    offset_file_name = offset_standard_information + length_standard_information
    type_file_name = int.from_bytes(mft_data[offset_file_name:offset_file_name + 4], byteorder='little')
    length_file_name = int.from_bytes(mft_data[offset_file_name + 4:offset_file_name + 8], byteorder='little')

    if (type_file_name != 48):
        offset_file_name = offset_file_name + length_file_name
        length_file_name = int.from_bytes(mft_data[offset_file_name + 4:offset_file_name + 8], byteorder='little')

    # location of the third attribute
    offset_data = offset_file_name + length_file_name
    type_data = int.from_bytes(mft_data[offset_data:offset_data + 4], byteorder='little')
    length_data = int.from_bytes(mft_data[offset_data + 4:offset_data + 8], byteorder='little')
    while type_data < 128:
        offset_data = offset_data + length_data
        type_data = int.from_bytes(mft_data[offset_data:offset_data + 4], byteorder='little')
        length_data = int.from_bytes(mft_data[offset_data + 4:offset_data + 8], byteorder='little')

    # Extract the flags (2 bytes) at offset 16
    flags = int.from_bytes(mft_data[0x16:0x18], byteorder='little')
    used = flags & 0x0001

    # Extract file permission (4 bytes) at offset 56 from the first attribute
    file_permission = int.from_bytes(mft_data[offset_standard_information + 56:offset_standard_information + 60], byteorder='little')
    system_file = (file_permission>>1 & 0x1)

    if (used == False or system_file == True):
        return None

    # Extract the ID (4 bytes) at offset 0x2C
    mft_entry_id = int.from_bytes(mft_data[0x2C:0x30], byteorder='little')

    # Extract the parent ID (6 bytes) at offset 24 from the second attribute
    parent_id = int.from_bytes(mft_data[offset_file_name + 24:offset_file_name + 30], byteorder='little')

    # Extract the parent sequence number (2 bytes) at offset 30 from the second attribute
    parent_sequence = int.from_bytes(mft_data[offset_file_name + 30:offset_file_name + 32], byteorder='little')

    # Extract the name length (1 byte) at offset 88 from the second attribute
    name_length = int.from_bytes(mft_data[offset_file_name + 88:offset_file_name + 89], byteorder='little')

    # Extract the name (variable length) at offset 90 from the second attribute
    try:
        name = mft_data[offset_file_name + 90:offset_file_name + 90 + name_length*2].decode('utf-16-le')
    except:
        return None
    
    resident = int.from_bytes(mft_data[offset_data + 8:offset_data + 9], byteorder='little')

    data = ''
    pattern = r"\.txt$"
    if re.search(pattern, name):
        if resident == 0:
            offset_data_start = offset_data + 24
            data_length = int.from_bytes(mft_data[offset_data + 16:offset_data + 18], byteorder='little')
            try:
                data = mft_data[offset_data_start:offset_data_start + data_length].decode('utf-8')
            except:
                data = mft_data[offset_data_start:offset_data_start + data_length].decode('utf-16-le')
        elif resident == 1:
            disk_path = fr'\\.\{disk_letter}:'
            offset_data_start = offset_data + 64
            first_cluster = 0
            while offset_data_start < offset_data + length_data:
                size = int.from_bytes(mft_data[offset_data_start:offset_data_start + 1], byteorder='little')
                if (size == 0):
                    break
                cluster_count_size = size & 0xF
                first_cluster_size = (size >> 4) & 0xF
                cluster_count = int.from_bytes(mft_data[offset_data_start + 1:offset_data_start + 1 + cluster_count_size], byteorder='little')
                first_cluster = int.from_bytes(mft_data[offset_data_start + 1 + cluster_count_size:offset_data_start + 1 + cluster_count_size + first_cluster_size], byteorder='little') + first_cluster
                offset_data_start = offset_data_start + 1 + cluster_count_size + first_cluster_size
                
                chunk = ''  # Use bytes instead of a string to preserve binary data

                # Đọc cluster_count bắt đầu tính từ first_cluster để lấy data
                with open(disk_path, 'rb') as f:
                    f.seek(first_cluster * sector_per_cluster * byte_per_sector, 0)
                    cluster_data = f.read(cluster_count * sector_per_cluster * byte_per_sector)
                    
                    # Find the position of the first occurrence of all zeros (0x00) in the cluster_data
                    zero_position = cluster_data.find(b'\x00\x00')  # Assuming you're working with binary data
                    
                    try:
                        if zero_position != -1:
                            if cluster_data.startswith(b'\xFF\xFE'):
                                # UTF-16 Little Endian BOM found
                                chunk = cluster_data[0:zero_position + 1].decode('utf-16-le')
                            elif cluster_data.startswith(b'\xFE\xFF'):
                                # UTF-16 Big Endian BOM found
                                chunk = cluster_data[0:zero_position].decode('utf-16-be')
                            else:
                                # No BOM found, default to UTF-8
                                chunk = cluster_data[0:zero_position].decode('utf-8')
                        else:
                            # No 0x00 sequence found, decode based on the BOM or default to UTF-8
                            if cluster_data.startswith(b'\xFF\xFE'):
                                # UTF-16 Little Endian BOM found
                                chunk = cluster_data.decode('utf-16-le')
                            elif cluster_data.startswith(b'\xFE\xFF'):
                                # UTF-16 Big Endian BOM found
                                chunk = cluster_data.decode('utf-16-be')
                            elif cluster_data.startswith(b'\EF\xBB\xBF'):
                                # UTF-8 BOM found
                                chunk = cluster_data.decode('utf-8')
                            else:
                                # No BOM found, default to UTF-8
                                chunk = cluster_data.decode('utf-8')
                    except:
                        chunk = ''

                data = data + chunk

    return TreeNode(mft_entry_id, sequence_number, parent_id, parent_sequence, name, data)
    
#============================Tree==================================
class TreeNode:
    def __init__(self, id, sequence, parent_id, parent_sequence, name, data = ''):
        self.id = id
        self.sequence = sequence
        self.parent_id = parent_id
        self.parent_sequence = parent_sequence
        self.name = name
        self.data = data
        self.children = []

def add_child_by_node(root, child):
    parent = find_node(root, child.parent_id, child.parent_sequence)
    if parent:
        parent.children.append(child)
        return True
    return False

#find a node by id and sequence number
def find_node(node, parent_id, parent_sequence):
    if node:
        if node.id == parent_id and node.sequence == parent_sequence:
            return node
        for child in node.children:
            result = find_node(child, parent_id, parent_sequence)
            if result:
                return result
    return None

#build a directory tree
def build_tree(id, sequence, parent_id, parent_sequence, name):
    root = TreeNode(id, sequence, parent_id, parent_sequence, name)
    nodes = []

    for i in range(24):
        mft_data = get_MFT(disk_letter, i)
        if (check_MFT(mft_data) == True):
            node = MFT_info(mft_data, disk_letter)
            if (node):
                nodes.append(node)
    
    i = 24
    while True:
        print(i)
        mft_data = get_MFT(disk_letter, i)
        i = i + 1
        if (check_MFT(mft_data) == True):
            node = MFT_info(mft_data, disk_letter)
            if (node):
                nodes.append(node)
        else:
            break
        
    while True:
        flag = False
        for node in nodes:
            if add_child_by_node(root, node):
                flag = True
                nodes.remove(node)
        if (flag == False):
            break
    
    return root

#print the file directory
def print_tree(node, depth=0, indent=''):
    if node:
        new_indent = indent + '|   ' if depth > 1 else ''
        print(f"{new_indent}{'|---' if depth > 0 else ''}{node.name}")
        for child in node.children:
            print_tree(child, depth + 1, new_indent)

def print_text_file(node):
    pattern = r"\.txt$"
    if node:
        if re.search(pattern, node.name):
            print(node.name, ':')
            print(node.data)
            print('---------------------------------------------------------------------')
        for child in node.children:
            print_text_file(child)


#============================Main==================================
disk_letter = "D"
#Read VBR Data from disk
vbr_data = read_vbr(disk_letter)
#Detect file system
fileSystemType = detect_filesystem_using_vbr(vbr_data)
if (fileSystemType == 'NTFS'):
    print_VBR_info(vbr_data)
    #Read MFT Data
    # Build the tree
    root_node = build_tree(5, 5, 0, 0, '.')

    # Print the tree
    print('File tree: ')
    print_tree(root_node)
    print('Text file data: ')
    print_text_file(root_node)
else:
    print("\nNot NTFS")

print("")

