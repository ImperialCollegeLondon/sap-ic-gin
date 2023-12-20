'''
This script converts tracking data from the .json format to a format easily
compatible with the TASCAR software [1]. Any missing data points (position
or orientation) are replaced by the sensor's previously held value. 

Modify this code to convert tracking data to a different format or change 
the missing data interpolation stategy.

[1] Grimm, Giso, et al. "Toolbox for acoustic scene creation and rendering
    (TASCAR): Render methods and research applications." Proceedings of the
    Linux Audio Conference. 2015.
'''

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import math
import csv
import json
import pandas as pd
import os
import copy
from datetime import datetime

def main():
    #----------- variables -----------#
    datafold='path_to_local_gin_database'

    if datafold=='path_to_local_gin_database':
    	raise NameError('Change local path to database in line 27!')
    speakerlist=['speaker1','speaker2','speaker3','speaker4','speaker5','speaker6','waiter']

    rooms=os.listdir(datafold)
    rooms = [i for i in rooms if 'room' in i]
    for room in rooms:
        sessions=os.listdir(os.path.join(datafold, room, 'tracked_data'))
        sessions=[i for i in sessions if 'session' in i]
        for session in sessions:
            outfold=os.path.join(datafold, room, 'tracked_data_tascar', session)

            if os.path.exists(outfold):
                print('Warning: Tascar directory already exists! Adding date to name')
                outfold=os.path.join(datafold, room, f"tracked_data_tascar_{datetime.now().strftime('%Y%m%d_%H%M%S')}", session)
            os.makedirs(outfold, exist_ok=True)

            files=os.listdir(os.path.join(datafold, room, 'tracked_data', session))
            files = sorted([i for i in files if i.endswith('.json')])

            lastdata=None
            for i in range(len(files)):
            	filename=files[i]
            	outpathroot = os.path.join(outfold, filename.split('.')[0])
            	with open(os.path.join(datafold, f'{room}', 'tracked_data', f'{session}', filename), 'r') as f:
            		alldata=json.load(f)
            	lastdata=jsontocsv(alldata, outpathroot, lastdata)

def jsontocsv(alldata, outpathroot, lastdata):
	flags=[]
	speakerlist=['speaker1','speaker2','speaker3','speaker4','speaker5','speaker6','waiter']
	storeddata=[]
	for speakeridx in range(len(speakerlist)):
		if lastdata is None:
			lastpos=[0,0,0]#get from previous file
			lastrot=[0,0,0]#get from previous file
		else:
			for d in lastdata:
				if d['participant']==speakeridx:
					lastpos=d['lastpos']
					lastrot=d['lastrot']
		with open(f"{outpathroot}_{speakerlist[speakeridx]}_position.csv", 'w', newline='') as csvfile:
			poswriter = csv.writer(csvfile, delimiter=',')
			for i in range(len(alldata)):
				# change to isnull
				if (alldata[i]['participant'][speakeridx]['position_x'])is None:
					poswriter.writerow([alldata[i]['time_stamp'],lastpos[0],lastpos[1],lastpos[2]])
					if (alldata[i]['participant'][speakeridx]['rotation_x'])is None:
						flags.append([alldata[i]['frame_number'], alldata[i]['time_stamp'], alldata[i]['participant'][speakeridx]['participant_id'], 1, 1])
					else:
						flags.append([alldata[i]['frame_number'], alldata[i]['time_stamp'], alldata[i]['participant'][speakeridx]['participant_id'], 1, 0])
				else:
					lastpos=[alldata[i]['participant'][speakeridx]['position_x'],alldata[i]['participant'][speakeridx]['position_y'],alldata[i]['participant'][speakeridx]['position_z']]
					poswriter.writerow([alldata[i]['time_stamp'],lastpos[0],lastpos[1],lastpos[2]])

		with open(f"{outpathroot}_{speakerlist[speakeridx]}_rotation.csv", 'w', newline='') as csvfile:
			rotwriter = csv.writer(csvfile, delimiter=',')
			for i in range(len(alldata)):
				if (alldata[i]['participant'][speakeridx]['rotation_x']) is None:
					rotwriter.writerow([alldata[i]['time_stamp'], lastrot[0], lastrot[1], lastrot[2]])
					if (alldata[i]['participant'][speakeridx]['position_x']) is None:
						flags.append([alldata[i]['frame_number'], alldata[i]['time_stamp'], alldata[i]['participant'][speakeridx]['participant_id'], 1, 1])
					else:
						flags.append([alldata[i]['frame_number'], alldata[i]['time_stamp'], alldata[i]['participant'][speakeridx]['participant_id'], 0, 1])
				else:
					lastrot=[alldata[i]['participant'][speakeridx]['rotation_z'],alldata[i]['participant'][speakeridx]['rotation_y'],alldata[i]['participant'][speakeridx]['rotation_x']]
					rotwriter.writerow([alldata[i]['time_stamp'], lastrot[0], lastrot[1], lastrot[2]])
		storeddata.append({'participant': speakeridx, 'lastpos': lastpos, 'lastrot':lastrot})
	return storeddata
if __name__=='__main__':
    main()
