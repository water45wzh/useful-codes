import sys
import json
import mido

def midifile_to_dict(mid):
    tracks = []
    for track in mid.tracks:
        tracks.append([vars(msg).copy() for msg in track])
    return {
        'ticks_per_beat': mid.ticks_per_beat,
        'tracks': tracks,
    }
    
mid = mido.MidiFile('midi_file.mid')
dict = midifile_to_dict(mid)
tempo = dict['tracks'][0][0]['tempo']
bom = 0

if (bpm == 0):
    bpm = mido.tempo2bpm(tempo)
else:
    tempo = mido.bpm2tempo(bpm)
    
print(json.dumps(
    {
        'code': 200, 'data': dict, 'bpm': int(bpm)
    },
    indent=2))