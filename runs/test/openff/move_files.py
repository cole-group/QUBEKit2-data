import os
import shutil


for i in range(1, 54):
    for root, dirs, files in os.walk('.', topdown=True):
        for di in dirs:
            if f'mol{str(i).zfill(2)}' in di and 'QUBE' in di:
                print(di)
                os.mkdir(f'mol{str(i).zfill(2)}')
                shutil.copy(f'{di}/10_finalise/mol{str(i).zfill(2)}.pdb', f'mol{str(i).zfill(2)}/mol{str(i).zfill(2)}.pdb')
                shutil.copy(f'{di}/10_finalise/mol{str(i).zfill(2)}.xml', f'mol{str(i).zfill(2)}/mol{str(i).zfill(2)}.xml')
