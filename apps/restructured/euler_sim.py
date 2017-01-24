#!/usr/bin/env python
import sys, os
from math import ceil

# Import local utility functions
#import opensbli as base
from opensbli.core import *
from opensbli.core.bcs import *
from opensbli.physical_models.euler_eigensystem import *
from sympy import *

BUILD_DIR = os.getcwd()

ndim = 2
weno = True
Euler_eq = EulerEquations(ndim, weno)

substitutions = []


coordinate_symbol = "x"

simulation_eq = SimulationEquations()
eq = Equation()

#WARNING: Not sure if the pressure in the momentum equation is being correctly evaluated 
# with the kronecker delta object, there is no pressure in the second parsed equation
for equation in Euler_eq.equations:
	eqns = eq.expand(equation, ndim, coordinate_symbol, substitutions, constants=Euler_eq.constants)
	pprint(eqns)
	print "-----------------------------------------------------------------"
	simulation_eq.add_equations(eqns)
constituent = ConstituentRelations()

for no, equation in enumerate(Euler_eq.formulas):
	pprint(no)
	print "Equation is: %s " % equation
	eqns = eq.expand(equation, ndim, coordinate_symbol, substitutions, constants=Euler_eq.constants)
	constituent.add_equations(eqns)
	print "------------------------------------------------------------------"
pprint(constituent.equations)

block= SimulationBlock(ndim, block_number = 0)

## Create eigensystem
ev_dict, LEV_dict, REV_dict = Euler_eq.generate_eig_system()
weno_order = 5
# Convert the system of equations into vector form
Euler_eq.eq_to_vector_form(simulation_eq.equations)
print "Vector form of the equations is:"
pprint(Euler_eq.vector_notation)

print "Formulae are :"
pprint(constituent.equations)

schemes = {}
LLF = LLFCharacteristic(ev_dict, LEV_dict, REV_dict, weno_order, ndim)
schemes[LLF.name] = LLF
cent = Central(4)
schemes[cent.name] = cent
rk = RungeKutta(3)
schemes[rk.name] = rk

cart = CoordinateObject('%s_i'%(coordinate_symbol))
coordinates = [cart.apply_index(cart.indices[0], dim) for dim in range(ndim)]

#WARNING: Currently, grouped equations, vector notation and required formula are generated in EulerEquations, 
# and then passed to GLF here. Need a better way to do it, make GLF dependent on Euler equations class or move 
# everything into Eigensystem inside WENO instead? Otherwise move the 3 eigensystems into EigenSystem class rather than
# in physical models? 

LLF.grouped_equations = LLF.group_by_direction(flatten(simulation_eq.equations))
LLF.vector_notation = Euler_eq.vector_notation
LLF.required_formulas = constituent.equations

# deriv = LLF.grouped_equations[0][0]

# pprint(deriv)
# direction = deriv.args[-1]
direction = coordinates[0]
direction_index = coordinates.index(direction)
side = -1

for direction in coordinates:
	direction_index = coordinates.index(direction)

	interpolations = LLF.pre_process(direction, direction_index)

	LLF.update_WenoSolutionType(interpolations)

	local_eval, reconstruction = LLF.post_process(interpolations)

exit()
block.sbli_rhs_discretisation = True
boundaries = [PeriodicBoundaryConditionBlock()]*2*ndim
block.set_block_boundaries(boundaries)
block.set_equations([simulation_eq])
block.set_discretisation_schemes(schemes)
block.discretise()

TraditionalAlgorithm(block)
# Create a descritisation class where the equations are deepcopied using deepcopy
#ex = copy.deepcopy(simulation_eq)
# block= SimulationBlock(ndim, block_number = 0)





#################

latex = LatexWriter()
latex.open('./equations.tex')
metadata = {"title": "Einstein Expansion of equations", "author": "Jammy", "institution": ""}
latex.write_header(metadata)
for index, eq in enumerate(flatten(simulation_eq.equations)):
    if isinstance(eq, Equality):
        latex.write_expression(eq)
latex.write_footer()
latex.close()


