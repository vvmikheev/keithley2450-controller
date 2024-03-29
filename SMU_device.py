import pyvisa
import numpy as np


class SMUDevice:

    def __init__(self, instruments_name):
        self.device = None
        self.instr_name = instruments_name
        self.connect(verbose=False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.device.close()

    def connect(self, verbose=True):
        """
            Connect to the device and make some preset. It has to be called after the class creation!
        """
        rm = pyvisa.ResourceManager()
        try:
            self.device = rm.open_resource(self.instr_name, write_termination = "\n")
        except pyvisa.errors.VisaIOError:
            print(f'Device {self.instr_name} is not present in the system, check the connections.')


        self.device.write('*RST')
        self.device.write('*CLS')
        self.device.write('*IDN?')
        device_info = self.device.read()

        if verbose:
            print(f'Device \n{device_info}is connected!')

    def write_command(self, command):
        self.device.write(command)

    def wait(self):
        """
            Waiting for the device to finish.
        """
        self.device.write('*OPC?')
        while True:
            try:
                self.device.read()
                break
            except pyvisa.errors.VisaIOError:
                continue

    def get_traces(self):
        self.device.write(':TRACe:ACTual:END?')
        ending_index = int(self.device.read())
        self.device.write(f':TRAce:DATA? 1, {ending_index}, "defbuffer1", RELative, SOURce, READing')
        result = self.device.read()
        result = result.split(',')
        result = list(map(float, result))
        data = {
            'time': result[::3],
            'source': result[1::3],
            'reading': result[2::3]
        }
        return data

    def setup_sense_subsystem(self, int_time=0.1, autorange=False, compl=1e-2, range=1e-3, counts=1):
        nplc_time = int_time / (1 / 60)  # 60 Hz power supply
        self.device.write(f'SENS:AZER:ONCE')
        self.device.write(f'SENS:CURR:AZER OFF')
        self.device.write(f'SENS:CURR:NPLC {max(0.01, nplc_time)}')

        if autorange:
            self.device.write(f'SENS:CURR:RANG:AUTO 1')
        else:
            self.device.write(f'SENS:CURR:RANG:AUTO 0')
            self.device.write(f'SENS:CURR:RANG {range}')

        self.device.write(f'SOUR:VOLT:ILIM {compl}')
        if counts != 1:
            self.device.write(f'SENS:COUNT {counts}')

    def setup_source_subsystem(self, range=20, autorange=False, readback=False, delay=0):
        self.device.write(f'SOUR:FUNC VOLT')
        self.device.write(f'SOUR:VOLT:RANG {range}')
        if autorange:
            self.device.write(f'SOUR:VOLT:RANG:AUTO ON')
        else:
            self.device.write(f'SOUR:VOLT:RANG:AUTO OFF')

        if delay is not None:
            self.device.write(f'SOUR:VOLT:DEL:AUTO OFF')
            self.device.write(f'SOUR:VOLT:DEL 0.001')
            self.device.write(f'SOUR:VOLT:DEL {delay}')
        else:
            self.device.write(f'SOUR:VOLT:DEL:AUTO ON')

        if readback:
            self.device.write(f'SOUR:VOLT:READ:BACK ON')
        else:
            self.device.write(f'SOUR:VOLT:READ:BACK OFF')

    def setup_staircase_sweep(self, v_from, v_to, n_steps, delay=1e-4):
        """
            set up staircase sweep (DC IV measurements)
            :param v_from: float (start value)
            :param v_to: float (start value)
            :param n_steps: int (number of steps)
            :param delay: float (delay between a voltage increase and a measurement)
        """
        self.device.write(f'SOUR:SWE:VOLT:LIN {v_from}, {v_to}, {n_steps}, {delay}, 1, AUTO')

    def setup_voltage_list_sweep(self, waveform, n_times):
        buffer_overrun = False
        waveforms = None
        n_points = len(waveform)

        if len(waveform) > 100:
            waveform_np = np.array(waveform)
            waveforms = np.array_split(waveform_np, int(np.ceil(len(waveform)/100)))
            buffer_overrun = True
            waveform = waveforms[0]

        waveform = map(str, waveform)
        waveform = ', '.join(waveform)

        self.device.write(f'SOUR:LIST:VOLT {waveform}')

        if buffer_overrun:
            for waveform in waveforms[1:]:
                waveform = map(str, waveform)
                waveform = ', '.join(waveform)
                self.device.write(f'SOUR:LIST:VOLT:APP {waveform}')

        self._define_sweep_trigger_model(n_points, n_times)

    def check_for_errors(self):
        """
            Check if some errors occurred during the measurements. Raise warning in that case.
            Errors might appear in reversed order.
        """
        self.device.write('SYST:ERR:COUN?')
        n_errors = int(self.device.read())
        if n_errors != 0:
            errors = []
            for i in range(n_errors):
                self.device.write('SYST:ERR:NEXT?')
                errors.append(self.device.read())
            errors = ''.join(errors)
            raise Warning(f'An error occurred during measurements:\n {errors}')

    def turn_on_display(self):
        self.device.write(f'DISP:LIGH:STAT ON50')

    def turn_off_display(self):
        self.device.write(f'DISP:LIGH:STAT BLAC')

    def set_terminal(self, name):
        if name == "rear":
            self.device.write('ROUT:TERM REAR')
        elif name == "front":
            self.device.write('ROUT:TERM FRON')
        else:
            raise Exception(f"Expected 'rear' or 'front', found {name}")

    def close(self):
        self.device.close()

    def _define_sweep_trigger_model(self, n_points, n_times, configuration_list="VoltCustomSweepList"):
        self.device.write('TRIG:LOAD "Empty"')
        self.device.write('TRIG:BLOC:BUFF:CLEAR 1')
        self.device.write(f'TRIG:BLOC:CONF:RECALL 2, "{configuration_list}"')
        self.device.write('TRIG:BLOC:SOUR:STAT 3, ON')
        self.device.write('TRIG:BLOC:BRAN:ALW 4, 6')
        self.device.write(f'TRIG:BLOC:CONF:NEXT 5, "{configuration_list}"')
        self.device.write('TRIG:BLOC:MEAS 6')
        self.device.write(f'TRIG:BLOC:BRAN:COUN 7, {n_points}, 5')
        self.device.write(f'TRIG:BLOC:BRAN:COUN 8, {n_times}, 2')
        self.device.write('TRIG:BLOC:SOUR:STAT 9, OFF')
        self.device.write('TRIG:BLOC:BRAN:ALW 10, 0')

