# 1. generate array of boundaries for x, y, and z
# 2. generate array of centroid (x,y,z), result, relative error
import argparse
import os

parser = argparse.ArgumentParser(prog = "MCNP mesh tally to .csv converter")
parser.add_argument("mcnpFile", type = str, help = "input mcnp .txt filename")
parser.add_argument("outputFile", type = str, help = "output .csv filename")

args = parser.parse_args()

# append output filename with .csv regardless of what its file extension is
output_filename, _ = os.path.splitext(args.outputFile)
output_filename += ".csv"

# open files
with open(args.mcnpFile, 'r') as mcnpFile, open(output_filename, 'w') as outputFile:
    # get array of boundaries for x,y,z
    # 1a. find line that has x boundaries
    mcnpLine = mcnpFile.readline()
    while "X direction:" not in mcnpLine:
        mcnpLine = mcnpFile.readline()
    # 1b. split line into all the boundaries, write to file with comma separation
    # do this 3 times for the 3 axes
    for a in range(3):
        boundariesArray = mcnpLine.split()
        outputStr = ""
        ba_length = len(boundariesArray)
        for index, boundary in enumerate(boundariesArray):
            if index >= 2 and index < ba_length-1:
                outputStr += boundary + ","
            elif index == ba_length-1:
                outputStr += boundary + "\n"
        outputFile.write(outputStr)
        mcnpLine = mcnpFile.readline()

    # advance to the centroid and results section
    while "Result" not in mcnpLine:
        mcnpLine = mcnpFile.readline()

    # 2. write all the centroid and result info to the csv file
    mcnpLine = mcnpFile.readline() # this will have the first centroid (x,y,z) and result
    # iterate through all voxels
    while mcnpLine:
        voxelArray = mcnpLine.split()
        outputStr = ""
        va_length = len(voxelArray)
        # write all data of a voxel with comma separation
        for index, data in enumerate(voxelArray):
            if index >= 1 and index < va_length-1:
                outputStr += data + ","
            elif index == va_length-1:
                outputStr += data + "\n"
        outputFile.write(outputStr)
        mcnpLine = mcnpFile.readline()


