import os
import sys

boot_sector_size = 512


#Read
try:
    with open("\\.D:",'rb') as f:
        boot_sector_data = f.read(boot_sector_size)
except FileNotFoundError:
    print(f"Error: Drive identifier not found.")
except PermissionError:
    print("Error: Permission denied. Run the script with appropriate privileges.")

# Init
jmp = boot_sector_data[0:2]
OEM_ID = boot_sector_data[3:10].decode() 
bytesPerSector = int.from_bytes(boot_sector_data[11:12])
sectorsPerCluster = int(boot_sector_data[13])
reservedSectors = boot_sector_data[14:15]
fatCopiesNum = boot_sector_data[16]
# 17:20: Not used
MediaDescriptor = boot_sector_data[21]
# 22:23: Not used
sectorPerTrack = int.from_bytes(boot_sector_data[24:25],"little")
heads = int.from_bytes(boot_sector_data[26:27],"little")
sectorsOnDisk =  int.from_bytes(boot_sector_data[28:31],"little")
sectorsInPar = int.from_bytes(boot_sector_data[32:35],"little")
sectorsPerFat = int.from_bytes(boot_sector_data[36:39],"little")
fatHandlingFlags = boot_sector_data[40:41]
#driveVersion = boot_sector_data[42:43].decode()
clusterNumForStartRootTable = int.from_bytes(boot_sector_data[44:47],"little")
sectorsNumFromSPartition1= boot_sector_data[48:49] # for the File System Information Sector
sectorsNumFromSPartition2 = boot_sector_data[50:51] #for the Backup Boot Sector
reversed = boot_sector_data[52:63]
logicalDriveNumber =boot_sector_data[64]
currentHead = boot_sector_data[65]
signature = boot_sector_data[66]
id = boot_sector_data[67:70]
volumeLabel = boot_sector_data[71:81]
systemID = boot_sector_data[82:89]

#Print:
print(f"OEM Name: {OEM_ID}")
print(f"bytesPerSector: {bytesPerSector}")
print(f"sectorsPerCluster: {sectorsPerCluster}")
