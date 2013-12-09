"""
prep_table_to_mesh_map prepares *.table and *.13 files needed for
T:**_manning.table-->fort.13 and creates the nxm matrix of multiplier
factors where n = # nodes, and m = # land classification values.
"""

import polysim.mesh_mapping.file_management as fm
import polysim.mesh_mapping.table_management as tm
import polysim.mesh_mapping.gridObject as go
import glob, subprocess, os
import polysim.utils.fort14_management as f14

# read in an input file that designates the following:
#   name of grid file
#   order to read in GAP/NLCD data file(s)
#   GAP/NLCD data file(s) with the associated data: THIS SHOULD BE A TUPLE
#       name of GAP/NLCD data file
#       name of classified value table
#       horizontal system
#       UTM Zone number
table = tm.read_table('rand_Manning.table')
gap_rect = tm.gapInfo('gap_data.asc', table)
gap_s1 = tm.gapInfo('sec1.asc', table)
gap_s2 = tm.gapInfo('sec2.asc', table)
gap_s3 = tm.gapInfo('sec3.asc', table)
gap_sec = tm.gapInfo('sections.asc',table)
gap_list = [gap_sec]
grid = go.gridInfo('flagged_fort.14', gap_list)
f14.flag_go(grid, 1)


convert_to_binary = True
first_landuse_folder_name = 'landuse_00'
first_script = fm.setup_landuse_folder(0, grid,
    folder_name = first_landuse_folder_name)
# run grid_all_data in this folder 
p = subprocess.Popen(['./'+first_script])
p.wait()
# set up remaining land-use classifications
script_list = fm.setup_landuse_folders(grid, False)

# THERE IS AN ERROR HERE WRT ODD/EVEN HANDLING FIX IT SEE SOLUTION IN
# RANDOM_MANNINGSN MODULE
#p = []
#for i in range(0, len(script_list), 2):
#    p.append(subprocess.Popen(['./'+script_list[i]]))
#    p.append(subprocess.Popen(['./'+script_list[i+1]]))
#    p[0].wait()
#    p[1].wait()
#    p = []

for s in script_list:
    subprocess.call(['./'+s])

binaries = glob.glob('*.asc.binary')
for f in binaries:
    os.remove(f)

subprocess.call(['./'+fm.setup_folder(grid,'test')])

# now clean out unecessary files and convert *.14 to *.13 when appropriate
fm.cleanup_landuse_folders(grid)
fm.convert(grid)
fm.rename13()

grid.convert('test')
fm.rename13(['test'])

