#!/usr/bin/python

# open a microphone in pyAudio and listen for taps

import pyaudio
import struct
import math
from scipy.signal import butter
from scipy.signal import lfilter_zi
from scipy.signal import lfilter
import numpy as np
from gi.repository import Notify


FORMAT = pyaudio.paInt16 
SHORT_NORMALIZE = (1.0/32768.0)
CHANNELS = 1
RATE = 44100 
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
LIMITE = 0.1
FREQ_LOW = 900
FREQ_HIGH = 1100
TIME_RINGING = 1
BLOCKS_RINGING = TIME_RINGING/INPUT_BLOCK_TIME


def design_filter(lowcut, highcut, fs, order=3):
    nyq = 0.5*fs
    low = lowcut/nyq
    high = highcut/nyq
    b,a = butter(order, [low,high], btype='band')
    return b,a

def normalize(block):
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )
    doubles = [x * SHORT_NORMALIZE for x in shorts]
    return doubles


def get_rms(samples):
    sum_squares = 0.0
    count = len(samples)/2
    
    for sample in samples:
        n = sample
        sum_squares += n*n
    return math.sqrt( sum_squares / count )

pa = pyaudio.PyAudio()                                 
stream = pa.open(format = FORMAT,                      
         channels = CHANNELS,                          
         rate = RATE,                                  
         input = True,                                 
         frames_per_buffer = INPUT_FRAMES_PER_BLOCK)   

errorcount = 0                                                  

# design the filter
b,a = design_filter(FREQ_LOW, FREQ_HIGH, RATE, 3)
# compute the initial conditions.
zi = lfilter_zi(b, a)

count_samples = 0 
while True:
    try:                                                    
        block = stream.read(INPUT_FRAMES_PER_BLOCK)         
    except IOError as e:                                      
        errorcount += 1                                     
        print( "(%d) Error recording: %s"%(errorcount,e) )  
        noisycount = 1          

    samples = normalize(block)                          

    bandpass_samples,zi = lfilter(b, a, np.array(samples), zi= zi*samples[0])

    amplitude = get_rms(samples)
    bandpass_ampl = get_rms(bandpass_samples)
    count_samples = count_samples+1

    if (bandpass_ampl > LIMITE) and count_samples > BLOCKS_RINGING:
        Notify.init ("Hello world")
        Hello=Notify.Notification.new ("Interfone",
                                    "Interfone tocando.",
                                    "dialog-information")
        # Hello.set_timeout(0)
        Hello.show ()
        print('amplitude aqui: ' + str(amplitude))
        print('Filtro: ' + str(bandpass_ampl))
        count_samples = 0
    
    if count_samples  == 200:
        count_samples = 20