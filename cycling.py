from SMU_device import SMUDevice
import time


def cycle(smu, n_times, vf, vs):
    params = {
        'Vf': vf,
        'Vs': vs,
        'n_cycles': 100,
    }

    waveform = [0, params['Vf'], params['Vf'], 0, 0, params['Vs'], params['Vs'], 0]
    smu.voltage_list_sweep(waveform, params['n_cycles'])

    smu.write_command('TRIG:LOAD "Empty"')
    smu.write_command('TRIG:BLOC:BUFF:CLEAR 1')
    smu.write_command('TRIG:BLOCK:CONF:RECALL 2, "VoltCustomSweepList"')
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
    instrument_id = r'USB0::0x05E6::0x2450::04130796::INSTR'
    smu = SMUDevice(r'USB0::0x05E6::0x2450::04130796::INSTR')
    smu.connect()

    params = {
            'Vf': 3,
            'Vs': -3,
            'n_cycles': 100,
        }

    waveform = [0, params['Vf'], params['Vf'], 0, 0, params['Vs'], params['Vs'], 0]
    smu.voltage_list_sweep(waveform, params['n_cycles'])

    smu.write_command('TRIG:LOAD "Empty"')
    smu.write_command('TRIG:BLOC:BUFF:CLEAR 1')
    smu.write_command('TRIG:BLOCK:CONF:RECALL 2, "VoltCustomSweepList"')
    smu.write_command('TRIG:BLOC:SOUR:STAT 3, ON')
    smu.write_command('TRIG:BLOC:CONF:NEXT 4, "VoltCustomSweepList"')
    smu.write_command(f'TRIG:BLOC:BRAN:COUN 5, {len(waveform) * params.get("n_cycles")}, 4 ')
    smu.write_command('TRIG:BLOC:SOUR:STAT 6, OFF')
    smu.write_command('TRIG:BLOC:BRAN:ALW 7, 0')


    smu.write_command('INIT')
    smu.check_for_errors()

    smu.wait()