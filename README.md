# stcontrol
Bose SoundTouch controls

## Functionality

This utility will search the local network for all SoundTouch speakers (using ZeroConf / Avahi / Bonjour), and join them
into a single zone. If nothing is playing, it will play a default preset, configured in `config.ini`. If there is no
configured default preset, it will use Preset 1.

## Setup
Install required packages

`pip install -r requirements.txt`

## Configuration

Copy `config_sample.ini` to `config.ini` and customize as needed

## Execute
Run:

`python main.py`
