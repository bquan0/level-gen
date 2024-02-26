# 1. generate array of boundaries for x, y, and z
# 2. generate array of centroid (x,y,z), result, relative error
import sys

# make sure the user entered the mcnp filename and the output filename as CLAs
if len(sys.argv) != 3:
    print("usage: python3 mcnp_to_csv.py <mcnp filename> <output .csv filename>")
    quit()

# append output filename with .csv if it doesn't end in .csv
output_filename = sys.argv[2]
if output_filename[-4:] != ".csv":
    output_filename = output_filename + ".csv"

# open files
mcnpFile = open(sys.argv[1], 'r')
outputFile = open(output_filename, 'w')


# get array of boundaries for x,y,z
# 1a. find line that has x boundaries
mcnpLine = mcnpFile.readline()
while mcnpLine.find("X direction:") == -1:
    mcnpLine = mcnpFile.readline()
# 1b. split line into all the boundaries, write to file with comma separation
# do this 3 times for the 3 axes
for a in range(3):
    boundariesArray = mcnpLine.split()
    outputStr = ""
    ba_length = len(boundariesArray)
    for index, boundary in enumerate(boundariesArray):
        if index >= 2 and index < ba_length-1:
            outputStr = outputStr + boundary + ","
        elif index == ba_length-1:
            outputStr = outputStr + boundary + "\n"
    outputFile.write(outputStr)
    mcnpLine = mcnpFile.readline()

# advance to the centroid and results section
while mcnpLine.find("Result") == -1:
    mcnpLine = mcnpFile.readline()

# 2. write all the centroid and result info to the csv file
mcnpLine = mcnpFile.readline() # this will have the first centroid (x,y,z) and result
# iterate through all voxels
while mcnpLine != "":
    voxelArray = mcnpLine.split()
    outputStr = ""
    va_length = len(voxelArray)
    # write all data of a voxel with comma separation
    for index, data in enumerate(voxelArray):
        if index >= 1 and index < va_length-1:
            outputStr = outputStr + data + ","
        elif index == va_length-1:
            outputStr = outputStr + data + "\n"
    outputFile.write(outputStr)
    mcnpLine = mcnpFile.readline()

mcnpFile.close()
outputFile.close()
