import os

BYTE_P_SECTOR = 512

def read_vbr(drive_letter):
    try:
        #filename = "03042023.txt"
        drive_path = fr'\\.\{drive_letter}:'

        with open(drive_path, 'rb') as f:
            # Read the VBR data
            boot_sector_data = f.read(BYTE_P_SECTOR)
            
            return boot_sector_data

    except FileNotFoundError:
        print(f"Error: Drive identifier {drive_letter} not found.")
    except PermissionError:
        print("Error: Permission denied. Run the script with appropriate privileges.")


######################################## MAIN  
drive_letter = "D"

# READ DISK
boot_sector_data = read_vbr(drive_letter)

# INIT
jmp = boot_sector_data[0:3]
OEM_ID = boot_sector_data[3:11].decode("utf-8") 
bytesPerSector = int.from_bytes(boot_sector_data[11:13],byteorder='little')
sectorsPerCluster = int.from_bytes(boot_sector_data[13:14],'little')
reservedSectors = int.from_bytes(boot_sector_data[14:16],'little')
fatsNum = int.from_bytes(boot_sector_data[16:17],'little')
# 17:21: Not used
mediaDescriptor = boot_sector_data[21:22].hex()
# 22:24: Not used
sectorPerTrack = int.from_bytes(boot_sector_data[24:26],"little")
headsNum = int.from_bytes(boot_sector_data[26:28],"little")
hiddenSectors =  int.from_bytes(boot_sector_data[28:32],"little")
totalSectors = int.from_bytes(boot_sector_data[32:36],"little")
sectorsPerFat = int.from_bytes(boot_sector_data[36:40],"little")
fatHandlingFlags = int.from_bytes(boot_sector_data[40:41],"little")
driveVersion = int.from_bytes(boot_sector_data[42:44],"little")
clusterNumForStartRootTable = int.from_bytes(boot_sector_data[44:48],"little")
systemInformation = int.from_bytes(boot_sector_data[48:50],"little") # for the File System Information Sector
backUpBootSector =int.from_bytes(boot_sector_data[50:52],"little") #for the Backup Boot Sector
reversed =int.from_bytes(boot_sector_data[52:63],"little")
physicalDrive = int.from_bytes(boot_sector_data[64:65],"little")
reverved =int.from_bytes(boot_sector_data[65:66],"little")
signature =int.from_bytes(boot_sector_data[66:67],"little")
id = boot_sector_data[67:71].hex()
volumeLabel = boot_sector_data[71:82].decode("utf-8")
systemID = boot_sector_data[82:90].decode("utf-8")

# PRINT 
offset = sectorsPerCluster*clusterNumForStartRootTable*bytesPerSector*512
try:
    filename = "03042023.txt"
    drive_path = fr'\\.\{drive_letter}:\{filename}'
    entry_data = None
    
    with open(drive_path, 'rb') as f:
        # Read the VBR data
        f.seek(offset)
        entry_data = f.read(32)
        filename = entry_data[:8].decode('utf-8').strip()
        file_extension = entry_data[8:11].decode('utf-8').strip()

        print(entry_data.hex())
        print(f"Name: {filename}.{file_extension}")

except FileNotFoundError:
    print(f"Error: Drive identifier {drive_letter} not found.")
except PermissionError:
    print("Error: Permission denied. Run the script with appropriate privileges.")
