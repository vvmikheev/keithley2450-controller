import numpy as np
from SMU_device import SMUDevice
from PUND_2_channels import mesure_PUND, cycle
import datetime
from plot_fig import *
import time

time.sleep(3)

smu_top = SMUDevice('SMU1')
smu_bottom = SMUDevice('SMU2')

area = 100 ** 2 * 1e-8
save = False
now = datetime.datetime.now()
save_name = f'{now.strftime("%m-%d-%y time-%H %M")}'
dir = os.path.join(os.getcwd(), "2021-03-10", "field7_c5_25um")


params = {
        'Vf': -3.5,
        'Vs': 3.5,
        'rise': 10,
        'hold': 20,
        'space': 20,
        'n_cycles': 2,
        'range_top': 1e-2,
        'range_bottom': 1e-6
        }


smu_top.set_terminal('front')
smu_bottom.set_terminal('front')

cycle(smu_top, smu_bottom, params, 100)
data = mesure_PUND(smu_top, smu_bottom, params)

converted = {'time': data['time'], 'source': data['voltage'], 'reading': - np.array(data['i_bottom'])}
plot_fig(converted, params, area, save=save, path=dir, name=save_name)

smu_top.close()
smu_bottom.close()