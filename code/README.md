# Supporting scripts

This folder contains useful scripts to use with the GiN data.

## VAD documentation

The VAD data in GiN were obtained automatically using the script provided in [generate_vad.py](generate_vad.py). This can be modified to use a different VAD implementation.

The [vad_documentation.ipynb](vad_documentation.ipynb) notebook provides details on the implementation of the VAD and shows examples of specific scenes.


## TASCAR tools
[TASCAR](https://www.tascar.org/) is an open-source toolbox for real-time rendering of virtual acoustic environments which may be useful in visualising and processing the GiN data. Some scripts are therefore provided to faciliate the use of GiN with TASCAR.

Instructions on how to install TASCAR can be found [here](https://www.tascar.org/install.html).

### Formatting the head-pose data

The raw head-pose data in GiN are given in a .json format not directly compatible with TASCAR. Instead, to describe head movements in TASCAR, two .csv files are required for each participant containing their head position and orientation. Additionally, TASCAR does not automatically extrapolate missing data points and these must be processed before use.

TASCAR-compatible data are already provided in the GiN dataset under the `tracked_data_tascar` folders. The missing data points were replaced using **forward filling**. The code used to obtain these data is given in [tracked_data_json_to_tascar.py](tracked_data_json_to_tascar.py) to allow for modification of the data interpolation procedure.


### Visualising scenes
Scenes can be visualised in Mac OS using the [fullscene.tsc](fullscene.tsc) and [launch_tascar.sh](launch_tascar.sh) scripts. 


To view a specific scene, e.g. `room_faraday/session_1/01_00_000`, use the following command from the `code` folder
```bash

./launch_tascar.sh path_to_GiN room_faraday session_1 01_00_000

```
