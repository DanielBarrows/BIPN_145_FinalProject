"""
Mind Monitor - OSC Receiver Audio Feedback
Coded: James Clutterbuck (2021)
Requires: python-osc, math, playsound, matplotlib, threading
"""
from pythonosc import dispatcher
from pythonosc import osc_server
import math
import pygame.mixer as pgm
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import threading
from datetime import datetime

#Network Variables
ip = "0.0.0.0"
port = 5000

#Muse Variables
hsi = [4,4,4,4]
hsi_string = ""
abs_waves = [-1,-1,-1,-1,-1]
rel_waves = [-1,-1,-1,-1,-1]

#Audio Variables
alpha_sound_play_chord = 0.4
alpha_sound_play_crash = 0.25


pgm.init(frequency=22050,size=-16,channels=4)
Chord = pgm.Sound("Reinforcement_Chord.mp3")
Crash = pgm.Sound("Crash.mp3")
chan0 = pgm.Channel(0)
chan1 = pgm.Channel(1)

f = open ('Daniel_Reinforcement_vs_punishment_1_RAW.csv','w+')

f2 = open('Daniel_Reinforcement_vs_punishment_alpha_1.csv','w+')

#Plot Array
plot_val_count = 200
plot_data = [[0],[0],[0],[0],[0]]

#Muse Data handlers
def hsi_handler(address: str,*args):
    global hsi, hsi_string
    hsi = args
    if ((args[0]+args[1]+args[2]+args[3])==4):
        hsi_string_new = "Muse Fit Good"
    else:
        hsi_string_new = "Muse Fit Bad on: "
        if args[0]!=1:
            hsi_string_new += "Left Ear. "
        if args[1]!=1:
            hsi_string_new += "Left Forehead. "
        if args[2]!=1:
            hsi_string_new += "Right Forehead. "
        if args[3]!=1:
            hsi_string_new += "Right Ear."        
    if hsi_string!=hsi_string_new:
        hsi_string = hsi_string_new
        print(hsi_string)    
          
def abs_handler(address: str,*args):
    global hsi, abs_waves, rel_waves
    wave = args[0][0]
    
    #If we have at least one good sensor
    if (hsi[0]==1 or hsi[1]==1 or hsi[2]==1 or hsi[3]==1):
        if (len(args)==2): #If OSC Stream Brainwaves = Average Onle
            abs_waves[wave] = args[1] #Single value for all sensors, already filtered for good data
        if (len(args)==5): #If OSC Stream Brainwaves = All Values
            sumVals=0
            countVals=0            
            for i in [0,1,2,3]:
                if hsi[i]==1: #Only use good sensors
                    countVals+=1
                    sumVals+=args[i+1]
            abs_waves[wave] = sumVals/countVals
            
        rel_waves[wave] = math.pow(10,abs_waves[wave]) / (math.pow(10,abs_waves[0]) + math.pow(10,abs_waves[1]) + math.pow(10,abs_waves[2]) + math.pow(10,abs_waves[3]) + math.pow(10,abs_waves[4]))
        update_plot_vars(wave)
        if (wave==2 and len(plot_data[0])>10) and chan0.get_busy() == True:
            pass
        #wait until audio is done playing before initiating next test
        elif (wave==2 and len(plot_data[0])>10) and chan0.get_busy() == False:
            test_alpha_relative_positive()
        if (wave==2 and len(plot_data[0])>10) and chan1.get_busy() == True:
            pass
        #wait until audio is done playing before initiating next test
        elif (wave==2 and len(plot_data[0])>10) and chan1.get_busy() == False:
            test_alpha_relative_negative()

#Audio test
def test_alpha_relative_positive():
    alpha_relative = rel_waves[2]
    if (alpha_relative<alpha_sound_threshold):
        print ("Not Focused:"+ "Alpha Relative: "+str(alpha_relative)+"----------"+ "Time: "+datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
    elif (alpha_relative>alpha_sound_threshold):
        print ("Focused:" + "Alpha Relative: "+str(alpha_relative)+"----------"+ "Time: "+datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
        pgm.Channel(0).play(Chord)
        
def test_alpha_relative_negative():
    alpha_relative = rel_waves[2]
    if (alpha_relative>alpha_sound_play_chord):
            Focused = ("Focused:"+ "Alpha Relative: "+str(alpha_relative)+"----------"+ "Time: " +datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
            print (Focused)
    elif (alpha_relative<alpha_sound_threshold):
            Not_Focused = ("Not_Focused:" + "Alpha Relative: "+str(alpha_relative)+"----------"+ "Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
            print (Not_Focused)
            pgm.Channel(1).play(Crash)
            
def writeFileHeader():
    global auxCount
    fileString = 'TimeStamp,RAW_TP9,RAW_AF7,RAW_AF8,RAW_TP10,'
    for x in range(0,auxCount):
        fileString += 'AUX'+str(x+1)+','
    fileString +='Marker\n'
    f.write(fileString)

def eeg_handler(address: str,*args):
    global recording
    global auxCount
    if auxCount==-1:
        auxCount = len(args)-4
        writeFileHeader()
    if recording:
        timestampStr = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        fileString = timestampStr
        for arg in args:
            fileString += ","+str(arg)
        fileString+="\n"
        f.write(fileString)

        alpha_relative = rel_waves[2]
        if (alpha_relative<alpha_sound_play_chord):
            Not_focused = ("Not Focused:"+ "Alpha Relative: "+str(alpha_relative)+"----------"+ "Time: "+datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
            Not_focused+="\n"
            f2.write(Not_focused)
        elif (alpha_relative>alpha_sound_play_crash):
            Focused= ("Focused:" + "Alpha Relative: "+str(alpha_relative)+"----------"+ "Time: "+datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
            Focused+="\n"
            f2.write(Focused)

        alpha_relative_negative = rel_waves[2]
        if (alpha_relative_negative>alpha_sound_play_crash):
            Focused = ("Focused:"+ "Alpha Relative: "+str(alpha_relative)+"----------"+ "Time: " +datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
            Focused+="\n"
            f2.write(Focused)
        elif (alpha_relative_negative<alpha_sound_play_crash):
            Not_Focused = ("Not_Focused:" + "Alpha Relative: "+str(alpha_relative)+"----------"+ "Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
            Not_Focused +="\n"
            f2.write(Not_Focused)            
            
            
#Live plot
def update_plot_vars(wave):
    global plot_data, rel_waves, plot_val_count
    plot_data[wave].append(rel_waves[wave])
    plot_data[wave] = plot_data[wave][-plot_val_count:]

def plot_update(i):
    global plot_data
    global alpha_sound_threshold
    if len(plot_data[0])<10:
        return
    plt.cla()
    for wave in [0,1,2,3,4]:
        if (wave==0):
            colorStr = 'red'
            waveLabel = 'Delta'
        if (wave==1):
            colorStr = 'purple'
            waveLabel = 'Theta'
        if (wave==2):
            colorStr = 'blue'
            waveLabel = 'Alpha'
        if (wave==3):
            colorStr = 'green'
            waveLabel = 'Beta'
        if (wave==4):
            colorStr = 'orange'
            waveLabel = 'Gamma'
        plt.plot(range(len(plot_data[wave])), plot_data[wave], color=colorStr, label=waveLabel+" {:.4f}".format(plot_data[wave][len(plot_data[wave])-1]))        
        
    plt.plot([0,len(plot_data[0])],[alpha_sound_threshold,alpha_sound_threshold],color='black', label='Alpha Sound Threshold',linestyle='dashed')
    plt.ylim([0,1])
    plt.xticks([])
    plt.title('Mind Monitor - Relative Waves')
    plt.legend(loc='upper left')
    
def init_plot():
    ani = FuncAnimation(plt.gcf(), plot_update, interval=100)
    plt.tight_layout()
    plt.show()
        
#Main
if __name__ == "__main__":
    #Tread for plot render - Note this generates a warning, but works fine
    thread = threading.Thread(target=init_plot)
    thread.daemon = True
    thread.start()
    
    #Init Muse Listeners    
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/muse/elements/horseshoe", hsi_handler)
    
    dispatcher.map("/muse/elements/delta_absolute", abs_handler,0)
    dispatcher.map("/muse/elements/theta_absolute", abs_handler,1)
    dispatcher.map("/muse/elements/alpha_absolute", abs_handler,2)
    dispatcher.map("/muse/elements/beta_absolute", abs_handler,3)
    dispatcher.map("/muse/elements/gamma_absolute", abs_handler,4)
    dispatcher.map("/muse/eeg", eeg_handler)
    
    server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher)
    print("Listening on UDP port "+str(port))
    server.serve_forever()
