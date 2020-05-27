from PUND_waveform import create_waveform
from SMU_device import SMUDevice
from plot_fig import plot_fig, save_data


smu = SMUDevice(r'USB0::0x05E6::0x2450::04130796::INSTR')
area = 50 ** 2 * 1e-8
save = False
save_name = 'contact_2B_new_exp'

"""
params is a dictionary with key parameters for a PUND sweep.

Vf - first voltage
Vs - second voltage
rise - number of measurements during the rise
hold - number of measurements to be done while maintaining the applied voltage
space - number of measurements between pulses
n_cycles - number of PUND cycles

Time required for a single measurement is approximately 0.5 ms. It is the limit for this SMU. The only way to control
rise/hold/space time is to change the number of measurements.
"""

params = {
        'Vf': 3,
        'Vs': -3,
        'rise': 20,
        'hold': 10,
        'space': 10,
        'n_cycles': 2
        }

waveform = create_waveform(params)
smu.setup_sense_subsystem(compl=1e-5, range=1e-5, int_time=0)
smu.setup_voltage_list_sweep(waveform, params['n_cycles'])

smu.write_command('INIT')
smu.wait()

smu.check_for_errors()
data = smu.get_traces()

plot_fig(data, params, area, save=save, path=dir, name=save_name)
if save:
    save_data(data, path=dir, name=save_name)