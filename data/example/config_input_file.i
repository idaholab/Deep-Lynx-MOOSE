# Copyright 2021, Battelle Energy Alliance, LLC

xmax = 3 # {{config}}

[Mesh]
  [gen]
    type = GeneratedMeshGenerator
    dim = 1 # {{config}}
    nx = 100 # {{config}}
    xmax = ${xmax} # {{config}}
  []
[]

[Variables]
  [u]
  []
[]

[Kernels]
  [diff]
    type = ADMatDiffusion
    variable = u
  []
[]

[BCs]
  [left]
    type = ADDirichletBC
    variable = u
    boundary = left
    value = 300 # {{config}}
  []
  [right]
    type = ADNeumannBC
    variable = u
    boundary = right
    value = 100 # {{config}}
  []
[]

[Materials]
  [mat]
    type = ADGenericFunctionMaterial
    prop_names = 'D'
    prop_values = 'x'
  []
[]

[Executioner]
  type = Steady
  solve_type = 'NEWTON'
[]

[VectorPostprocessors]
  [temp_line]
    type = LineValueSampler
    variable = u
    sort_by = x
    start_point = '0 0 0'
    end_point = '${xmax} 0 0'
    num_points = 200 # {{config}}
  []
[]

[Postprocessors]
  [temp_mid]
    type = PointValue
    variable = u
    point = '1.5 0 0'
  []
  [temp_max]
    type = NodalExtremeValue
    variable = u
    value_type = max
  []
  [temp_min]
    type = NodalExtremeValue
    variable = u
    value_type = min
  []
  [temp_avg]
    type = AverageNodalVariableValue
    variable = u
  []
[]

[Outputs]
  [out]
    type = JSON
    postprocessors_as_reporters = true
    vectorpostprocessors_as_reporters = true
    file_base = output/sockeye_run_out
  []
[]
