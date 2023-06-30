# Illustates the third example from the README.md page, using
# defaults from a file.
# Should work if run from the directory containing this file
# in the tomlparams repo.


from tomlparams import TOMLParams

params = TOMLParams(
    defaults='defaults', name='newparam', standard_params_dir=''
)
