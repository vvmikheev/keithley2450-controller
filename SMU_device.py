import pyvisa
import numpy as np


class SMUDevice:

    def __init__(self, instruments_name):
        self.device = None
        self.instr_name = instruments_name

    def connect(self, verbose=True):
        """
            Connect to the device and make some preset. It has to be called after the class creation!
        """
        rm = pyvisa.ResourceManager()
        try:
            self.device = rm.open_resource(self.instr_name)
        except pyvisa.errors.VisaIOError:
            print(f'Device {self.instr_name} is not present in the system, check the connections.')

        # self.device.write('*RST', 0)
        self.device.write('*CLS', 0)
        self.device.write('*IDN?', 0)
        device_info = self.device.read()

        if verbose:
            print(f'Device \n{device_info}is connected!')

    def write_command(self, command):
        self.device.write(command, 0)

    def wait(self):
        """
            Waiting for the device to finish.
        """
        self.device.write('*OPC?', 0)
        while True:
            try:
                self.device.read()
                break
            except pyvisa.errors.VisaIOError:
                continue

    def get_traces(self):
        self.device.write(':TRACe:ACTual:END?', 0)
        ending_index = int(self.device.read())
        self.device.write(f':TRAce:DATA? 1, {ending_index}, "defbuffer1", RELative, SOURce, READing', 0)
        result = self.device.read()
        result = result.split(',')
        result = list(map(float, result))
        data = {
            'time': result[::3],
            'source': result[1::3],
            'reading': result[2::3]
        }
        return data

    def setup_sense_subsystem(self, int_time=0.1, autorange=False, compl=1e-2, range=1e-3):
        nplc_time = int_time / (1 / 60)  # 60 Hz power supply
        self.device.write(f'SENS:AZER:ONCE', 0)
        self.device.write(f'SENS:CURR:AZER OFF', 0)
        self.device.write(f'SENS:CURR:NPLC {max(0.01, nplc_time)}', 0)
        self.device.write(f'SOUR:VOLT:ILIM {compl}', 0)
        if autorange:
            self.device.write(f'SENS:CURR:RANG:AUTO 1', 0)
        else:
            self.device.write(f'SENS:CURR:RANG:AUTO 0', 0)
            self.device.write(f'SENS:CURR:RANG {range}', 0)

    def setup_staircase_sweep(self, v_from, v_to, n_steps, delay=1e-4):
        """
            set up staircase sweep (DC IV measurements)
            :param v_from: float (start value)
            :param v_to: float (start value)
            :param n_steps: int (number of steps)
            :param delay: float (delay between a voltage increase and a measurement)
        """
        self.device.write(f'SOUR:VOLT:RANG:AUTO ON', 0)
        self.device.write(f'SOUR:VOLT:READ:BACK ON', 0)
        self.device.write(f'SOUR:SWE:VOLT:LIN {v_from}, {v_to}, {n_steps}, {delay}, 1, AUTO', 0)

    def setup_voltage_list_sweep(self, waveform, n_times, dt=0, read_back=False):
        buffer_overrun = False
        waveforms = None

        if len(waveform) > 100:
            waveform_np = np.array(waveform)
            waveforms = np.array_split(waveform_np, int(np.ceil(len(waveform)/100)))
            buffer_overrun = True
            waveform = waveforms[0]

        waveform = map(str, waveform)
        waveform = ', '.join(waveform)

        self.device.write(f'SOUR:FUNC VOLT', 0)
        self.device.write(f'SOUR:VOLT:RANG 20', 0)
        self.device.write(f'SOUR:VOLT:RANG:AUTO OFF', 0)
        self.device.write(f'SOUR:VOLT:DEL:AUTO OFF')
        self.device.write(f'SOUR:VOLT:DEL 0.001')
        self.device.write(f'SOUR:VOLT:DEL 0')

        if read_back:
            self.device.write(f'SOUR:VOLT:READ:BACK ON', 0)
        else:
            self.device.write(f'SOUR:VOLT:READ:BACK OFF', 0)
        self.device.write(f'SOUR:LIST:VOLT {waveform}', 0)

        if buffer_overrun:
            for waveform in waveforms[1:]:
                waveform = map(str, waveform)
                waveform = ', '.join(waveform)
                self.device.write(f'SOUR:LIST:VOLT:APP {waveform}')

        self.device.write(f'SOUR:SWE:VOLT:LIST 1, {dt}, {n_times}', 0)

    def check_for_errors(self):
        """
            Check if some errors occurred during the measurements. Raise warning in that case.
            Errors might appear in reversed order.
        """
        self.device.write('SYST:ERR:COUN?', 0)
        n_errors = int(self.device.read())
        if n_errors != 0:
            errors = []
            for i in range(n_errors):
                self.device.write('SYST:ERR:NEXT?', 0)
                errors.append(self.device.read())
            errors = ''.join(errors)
            raise Warning(f'An error occurred during measurements:\n {errors}')

    def turn_on_display(self):
        self.device.write(f'DISP:LIGH:STAT ON50', 0)

    def turn_off_display(self):
        self.device.write(f'DISP:LIGH:STAT BLAC', 0)


