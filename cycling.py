from SMU_device import SMUDevice
import time


def cycle(smu, n_times, vf, vs):
    params = {
        'Vf': vf,
        'Vs': vs,
        'n_cycles': n_times,
    }

    waveform = [0, params['Vf'], params['Vf'], 0, 0, params['Vs'], params['Vs'], 0]
    smu.setup_sense_subsystem(int_time=0, compl=1e-4, range=1e-4)
    smu.setup_voltage_list_sweep(waveform, params['n_cycles'])

    smu.write_command('TRIG:LOAD "Empty"')
    smu.write_command('TRIG:BLOC:BUFF:CLEAR 1')
    smu.write_command('TRIG:BLOC:CONF:RECALL 2, "VoltCustomSweepList"')
    smu.write_command('TRIG:BLOC:SOUR:STAT 3, ON')
    smu.write_command('TRIG:BLOC:CONF:NEXT 4, "VoltCustomSweepList"')
    smu.write_command(f'TRIG:BLOC:BRAN:COUN 5, {len(waveform) * params.get("n_cycles")}, 4 ')
    smu.write_command('TRIG:BLOC:SOUR:STAT 6, OFF')
    smu.write_command('TRIG:BLOC:BRAN:ALW 7, 0')

    smu.write_command('INIT')
    smu.check_for_errors()

    smu.wait()


if __name__ == '__main__':
    time.sleep(0)
    instrument_id = 'SMU'
    smu = SMUDevice(instrument_id)
    smu.connect()

    smu.set_terminal('front')
    cycle(smu, 10, 1, -1)