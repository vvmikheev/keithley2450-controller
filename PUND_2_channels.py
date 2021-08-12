import numpy as np
from PUND_waveform import create_waveform
import time
from scipy.interpolate import interp1d


def _top_smu_trigger_model(smu, n_points, n_times):
    smu.device.write('TRIG:LOAD "Empty"')
    smu.device.write('TRIG:BLOC:BUFF:CLEAR 1')
    smu.device.write('TRIG:BLOC:NOT 2, 1')
    smu.device.write(f'TRIG:BLOC:CONF:RECALL 3, "VoltCustomSweepList"')
    smu.device.write('TRIG:BLOC:SOUR:STAT 4, ON')
    smu.device.write('TRIG:BLOC:BRAN:ALW 5, 7')
    smu.device.write(f'TRIG:BLOC:CONF:NEXT 6, "VoltCustomSweepList"')
    smu.device.write('TRIG:BLOC:MEAS 7')
    smu.device.write(f'TRIG:BLOC:BRAN:COUN 8, {n_points}, 6')
    smu.device.write(f'TRIG:BLOC:BRAN:COUN 9, {n_times}, 2')
    smu.write_command('TRIG:BLOC:NOT 10, 2')
    smu.device.write('TRIG:BLOC:SOUR:STAT 11, OFF')
    smu.device.write('TRIG:BLOC:BRAN:ALW 12, 0')

    # notification channels might be redefined
    smu.write_command(':DIG:LINE1:MODE TRIG, OUT')
    smu.write_command(':DIG:LINE2:MODE TRIG, OUT')
    smu.write_command('TRIG:DIG1:OUT:STIM NOTify1')  # signal to start measurements
    smu.write_command('TRIG:DIG2:OUT:STIM NOTify2')  # signal to finish measurements


def _bottom_smu_trigger_model(smu):
    # event channels (must be equal to channels in _top_smu_trigger_model)
    smu.write_command(':DIG:LINE1:MODE TRIG, IN')
    smu.write_command(':DIG:LINE2:MODE TRIG, IN')
    start_event = 'DIG 1'  # start measurements
    stop_event = 'DIG 2'  # measure until

    smu.device.write('TRIG:LOAD "Empty"')
    smu.device.write('TRIG:BLOC:BUFF:CLEAR 1')
    smu.device.write(f'TRIG:BLOC:WAIT 2, {start_event}')
    smu.device.write(f'TRIG:BLOC:CONF:RECALL 3, "VoltCustomSweepList"')
    smu.device.write('TRIG:BLOC:SOUR:STAT 4, ON')
    smu.device.write('TRIG:BLOC:MEAS 5')
    smu.device.write(f'TRIG:BLOC:BRAN:EVEN 6, {stop_event}, 8')
    smu.device.write('TRIG:BLOC:BRAN:ALW 7, 5')
    smu.device.write('TRIG:BLOC:SOUR:STAT 8, OFF')
    smu.device.write('TRIG:BLOC:BRAN:ALW 9, 0')


def mesure_PUND(smu_top, smu_bottom, params):

    waveform = create_waveform(params, by_rate=True)
    smu_top.setup_voltage_list_sweep(waveform, params['n_cycles'])

    _top_smu_trigger_model(smu_top, len(waveform), params['n_cycles'])
    _bottom_smu_trigger_model(smu_bottom)

    smu_bottom.write_command('INIT')
    time.sleep(0.1)
    smu_top.write_command('INIT')
    smu_top.wait()
    smu_bottom.wait()

    data_bottom = smu_bottom.get_traces()
    data_top = smu_top.get_traces()

