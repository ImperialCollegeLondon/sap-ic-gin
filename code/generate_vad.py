'''
This script generates the VAD data from the GiN database using the Silero 
Voice Activity Detector in [1]. There is also an option to add automatic
transcription using Open AI's Whisper [2].

The VAD contains a cross-channel energy threshold, alpha, empirically set
to alpha=0.2. The automatic transcription can be toggled and is not used 
by default to reduce the script's run-time. 

Modify this code to change the alpha parameter, use a different VAD system
or ASR model.

[1] Silero Tean, "Silero VAD: pre-trained entrprise-grade Voice Activity
    Detector (VAD), Number Detector and Language Classifier." Github
    repository. 2021. [Online] https://github.com/snakers4/silero-vad
[2] Radford, Alec, et al. "Robust speech recognition via large-scale
    weak supervision." International Conference on Machine Learning. PMLR,
    2023.
'''
import torch
torch.set_num_threads(1)
import os
import glob
import re
import csv
import scipy.io
import sys
from IPython.display import Audio
from pprint import pprint

import torchaudio
from typing import Callable, List
import torch.nn.functional as F
import warnings
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.colors as mcolors
import numpy as np
import math
import copy
import warnings
warnings.filterwarnings('ignore')
import torch
import pandas as pd
import whisper
import ssl
import json
from datetime import datetime

def main():
    #----------- variables -----------#
    datafold='path_to_local_gin_database'

    if datafold=='path_to_local_gin_database':
        raise NameError('Change local path to database in line 52!')

    alpha=float(0.2)
    transcription_toggle=0

    #----------- VAD setup -----------#
    # this assumes that you have a relevant version of PyTorch installed
    # !pip install -q torchaudio


    USE_ONNX = False # change this to True if you want to test onnx model
    # if USE_ONNX:
        # !pip install -q onnxruntime
      
    vadmodel, vadutils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                  model='silero_vad',
                                  force_reload=True,
                                  onnx=USE_ONNX)


    #----------- ASR setup -----------#
    if transcription_toggle:
        asrmodel = whisper.load_model("medium.en")
        print(
            f"Model is {'multilingual' if model.is_multilingual else 'English-only'} "
            f"and has {sum(np.prod(p.shape) for p in model.parameters()):,} parameters."
        )
        asroptions = whisper.DecodingOptions(language="en", without_timestamps=True)
    else:
        asrmodel = None

    # loop through rooms and sessions and files run vad
    rooms=os.listdir(datafold)
    rooms = [i for i in rooms if 'room' in i]
    for room in rooms:
        sessions=os.listdir(os.path.join(datafold, room, 'close_talking_audio'))
        sessions=[i for i in sessions if 'session' in i]

        for session in sessions:
            outfold=os.path.join(datafold, room, f'vad_data', session)
            if os.path.exists(outfold):
                print('Warning: VAD directory already exists! Adding date to name')
                outfold=os.path.join(datafold, room, f"vad_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}", session)
            os.makedirs(outfold, exist_ok=True)

            files=os.listdir(os.path.join(datafold, room, 'close_talking_audio', session))
            files = [i for i in files if i.endswith('.wav')]

            for i in range(len(files)):
                filename=files[i]

                outfile = os.path.join(outfold, filename.split('.')[0]+'.json')

                audiopath=[os.path.join(datafold,room,'close_talking_audio',session,filename),
                os.path.join(datafold,room,'waiter_audio',session,filename)]

                metadatafile=os.path.join(datafold, room, 'metadata', session,'tasktimings.csv')

                # run the VAD
                vaddict=run_vad(audiopath,metadatafile, vadmodel=vadmodel, vadutils=vadutils, alpha=alpha, asrmodel=asrmodel)
                with open(outfile, 'w', encoding='utf-8') as f:
                    json.dump(vaddict, f, ensure_ascii=False, indent=4)


def run_vad(audiopath, metadatafile,**kwargs):

    vadmodel=kwargs.get('vadmodel')
    vadutils=kwargs.get('vadutils')

    if 'alpha' in kwargs:
        alpha = kwargs.get('alpha')
    else:
        alpha = float(0.2)

    filestarttime=float(audiopath[0].split(os.sep)[-1][0:-4].split('_')[0])*60+float(audiopath[0].split(os.sep)[-1][0:-4].split('_')[1])+float(audiopath[0].split(os.sep)[-1][0:-4].split('_')[2])/1000

    tasktimings=[]
    with open(metadatafile, 'r', encoding='utf-8-sig') as csvfile:
        reader=csv.DictReader(csvfile)
        for row in reader:
            tasktimings.append(row)

    #----------- VAD setup -----------#
    (get_speech_timestamps,
     save_audio,
     read_audio,
     VADIterator,
     collect_chunks) = vadutils
    #----------- ASR setup -----------#
    if 'asrmodel' in kwargs:
        asrmodel=kwargs.get('asrmodel')
    else:
        asrmodel=None
    #----------- load audio -----------#
    wavclose,fs=torchaudio.load(audiopath[0])
    wavwaiter,__=torchaudio.load(audiopath[1])

    wav=torch.cat((wavclose,wavwaiter),0)
    #----------- get the VAD output -----------#
    SPEECHES=[]
    for j in range(wav.size(0)):
        WAV=wav[j,:]
        window_size_samples=1536
        speech_probs = []
        speeches=get_speech_timestamps(audio=WAV,model=vadmodel, sampling_rate=fs,
                                                         window_size_samples=window_size_samples)
        SPEECHES.append(speeches)

    speechmatrix=np.zeros((wav.size(0),fs*60))
    for i in range(wav.size(0)):
        for j in range(len(SPEECHES[i])):
            speechmatrix[i,range(SPEECHES[i][j]["start"],SPEECHES[i][j]["end"],1)]=1

    #----------- adjust the VAD output -----------#
    adjustedspeechmatrix=speechmatrix.copy()
    adjustedspeechtimestamps=copy.deepcopy(SPEECHES)

    val=np.empty((7))
    for i in range(wav.size(0)):
        k=0
        for j in range(len(SPEECHES[i])):
            for l in range(wav.size(0)):
                val[l]=torch.mean(torch.abs(wav[l,SPEECHES[i][j]["start"]:SPEECHES[i][j]["end"]])**2)+torch.std(torch.abs(wav[l,SPEECHES[i][j]["start"]:SPEECHES[i][j]["end"]])**2)

            if (any(val[i]<x for x in alpha*val)):
                adjustedspeechmatrix[i,SPEECHES[i][j]["start"]:SPEECHES[i][j]["end"]]=0
                adjustedspeechtimestamps[i].pop(k)
            else:
                k+=1

    #----------- build the dictionary -----------#
    vaddict=[]
    for i in range(wav.size(0)):
        for j in range(len(adjustedspeechtimestamps[i])):
            if i==6:
                speaker='waiter'
            else:
                speaker=f'speaker{i+1}'

            taskid=list(filter(lambda k: float(k['start_time'])<filestarttime+(adjustedspeechtimestamps[i][j]["start"]/fs), tasktimings))[-1]['task_id']

            if asrmodel is None:
                entry={"start_sample_index":adjustedspeechtimestamps[i][j]["start"]+1,
               "end_sample_index":adjustedspeechtimestamps[i][j]["end"],
               "participant_id":speaker,
               "task_id": taskid}
            else:
                save_audio('temp.wav',
                   wav[i,adjustedspeechtimestamps[i][j]["start"]:adjustedspeechtimestamps[i][j]["end"]], sampling_rate=fs) 
                result=asrmodel.transcribe('temp.wav')
            
                entry={"start_sample_index":adjustedspeechtimestamps[i][j]["start"]+1,
                       "end_sample_index":adjustedspeechtimestamps[i][j]["end"],
                       "participant_id":speaker,
                       "task_id": taskid,
                      "transcription": result["text"]}
            vaddict.append(entry)

    vaddict=sorted(vaddict, key=lambda k: k['start_sample_index'])
    return vaddict

if __name__=='__main__':
    main()