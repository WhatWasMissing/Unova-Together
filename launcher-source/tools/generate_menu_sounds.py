"""Generate small original launcher feedback tones using only Python's stdlib."""
from pathlib import Path
import math
import struct
import wave

ASSETS=Path(__file__).resolve().parent/'launcher_ui'/'assets'
RATE=22050

def tone(notes):
    samples=[]
    for frequency,duration in notes:
        count=round(RATE*duration)
        fade=max(1,round(RATE*.006))
        for index in range(count):
            envelope=min(1.0,index/fade,(count-1-index)/fade)
            sample=round(5200*max(0.0,envelope)*math.sin(2*math.pi*frequency*index/RATE))
            samples.append(max(-32768,min(32767,sample)))
    return b''.join(struct.pack('<h',sample) for sample in samples)

def main():
    ASSETS.mkdir(parents=True,exist_ok=True)
    cues={
        'nav':[(740,.035)],
        'confirm':[(660,.045),(990,.055)],
        'cancel':[(820,.045),(520,.060)],
    }
    for name,notes in cues.items():
        with wave.open(str(ASSETS/f'menu-{name}.wav'),'wb') as output:
            output.setnchannels(1);output.setsampwidth(2);output.setframerate(RATE)
            output.writeframes(tone(notes))

if __name__=='__main__':main()
