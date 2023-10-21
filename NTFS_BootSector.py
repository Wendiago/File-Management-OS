import os
BYTE_P_SECTOR = 512
mft_cluster = None
        
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
    global mft_cluster
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
    print("Sectors per track", int.from_bytes(bpb_data[13:15], byteorder='little'))
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
        
def read_vbr(drive_letter):
    try:
        drive_path = fr'\\.\{drive_letter}:'

        with open(drive_path, 'rb') as f:
            # Read the VBR data
            vbr_data = f.read(512)
            
            return vbr_data

    except FileNotFoundError:
        print(f"Error: Drive identifier {drive_letter} not found.")
    except PermissionError:
        print("Error: Permission denied. Run the script with appropriate privileges.")

#============================Main==================================
drive_letter = "C"
# Print VBR
vbr_data = read_vbr(drive_letter)
print_VBR_info(vbr_data)

#Get mft cluster number
print("\nMFT cluster number: ", mft_cluster)