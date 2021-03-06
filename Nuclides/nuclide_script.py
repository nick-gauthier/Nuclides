import grass.script as grass
import grass.script.array as garray
import numpy as np
#from multiprocessing import Pool
import matplotlib.pyplot as plt


elev_init = 'DEM' # initial elevation map for t=0
bedrock = 'bedrock' # bedrock elevation map from r.soildepth.py
coor = '725763.609242,4284801.3547' # "727195.790391, 4285699.45461" # location(s) at which to take a virtual sediment core

grass.run_command('g.region', res = 10)

# define an intial value for the nuclide concentrations
init = 1

grass.mapcalc('soildepth_init = if({} - {} < 0, 0, {} - {})'.format(elev_init, bedrock, elev_init, bedrock), overwrite=True)                                                                
core_init_depth = int(float(grass.read_command('r.what', map = 'soildepth_init', coordinates = coor, separator = ',').strip().split(',')[3]) * 100)

init_depths = garray.array()
init_depths.read('soildepth_init')
init_depths = (init_depths * 100).astype(int)

# convert to integer
make_column = np.vectorize(lambda x: [init] * x, otypes=[np.ndarray])
soil_columns = make_column(init_depths)

core_column = make_column(core_init_depth)

# in situ be10 formula
# Setup parameters
P_0 = 4.49		# production rate of Beryllium-10 in quartz at sea level [at/g/yr] after Stone, 1999.
ltlambda = np.log(2) / 1.5e6 # decay constant
L = 160. 	# absorption mean-free path (attentuation length)  [g/cm2]   
p = 2.6 	# density of overburden [ g/cm3]

#create a dummy map that has the surface elevation for all cells

def b10_situ(column):
    if column:
        for depth,value in enumerate(column):
            column[depth] += P_0 * np.exp(-1 * depth * L / p) - value * ltlambda

#pool = Pool(processes=4)
#timeit pool.map(b10_situ, soil_columns)


b10_situ = np.vectorize(b10_situ)
b10_situ(soil_columns)

#timeit b10_situ(soil_columns)
#timeit ne.evaluate("b10_situ(soil_columns)")



#get list of elevation maps
elevmaps = grass.read_command('g.list', flags='m', type='rast', pattern='levol_elevation*', separator=',').strip().split(',')
edmaps = grass.read_command('g.list', flags='m', type='rast', pattern='levol_ED_rate*', separator=',').strip().split(',')
soildepthmaps = grass.read_command('g.list', flags='m', type='rast', pattern='levol_soildepth*', separator=',').strip().split(',')


grass.run_command('r.series', overwrite=True, input=edmaps, output='erosion_total', method='sum')

grass.run_command("r.watershed", quiet=True, overwrite=True, elevation=elevmaps[49], drainage="fldr_tmp")
# generate basin for sample coordinates
grass.run_command("r.water.outlet", quiet=True, overwrite=True, input="fldr_tmp", output='basin_tmp', coordinates=coor)
    
# mask to upstream basin
grass.run_command('r.mask', raster = 'basin_tmp', overwrite = True)

# find out which cells experienced any erosion
grass.mapcalc('eroded_cells = if(erosion_total < 0, erosion_total, null())', overwrite = True)

erosion = garray.array()
erosion.read('eroded_cells')
erosion *= 100
erosion = erosion.astype(int)

grass.run_command('r.mask', flags = 'r')

deposition = float(grass.read_command('r.what', map = 'erosion_total', coordinates = coor, separator = ',').strip().split(',')[3]) * 100


plt.imshow(erosion)

# next need to loop through soil columns, average values according to erosion, and add deposition cells to top of virtual core with same value


# calculate topo shielding using r.skyview
#r.skyview input=DEM output=shielding ndir=16

### more vectorized be10 script
test_col = [4,3,2,1,0]

test_col += P_0 * np.exp(-1 * depth * L / p) - test_col * ltlambda

for depth,value in enumerate(test_col):
            column[depth] += P_0 * np.exp(-1 * depth * L / p) - value * ltlambda


def return_number(my_number):
    return my_number += P_0 * np.exp(-1 * depth * L / p) - test_col * ltlambda


def add_number(my_list):

    if isinstance(my_list, (int, float)):
        return return_number(my_list)
    else:
        return [add_number(xi) for xi in my_list]



A = [[[0, 0, 0], [0, 0, 0], [0, 0, 0]], [[0], [0], [0]]]

add_number(A)
A

