#!/usr/bin/python3
"""
PySonde
Licensed under GNU AGPLv3
Full copy of the license is in the LICENSE file.
Author: Blagus
"""

version = "v0.1"

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter.scrolledtext import *
from tkinter.messagebox import *
import socket
import struct, threading, queue, scipy.io.wavfile, numpy, pylab
from timeit import default_timer as timer

class GUI:
    def __init__(self, master):
        self.wavstream = []
        self.master = master
        self.UDP_active = False
        frameControl = Frame(master)
        frameControl.pack(side=LEFT, anchor=NW)
        frameOutput = Frame(master)
        frameOutput.pack(side=RIGHT)
        self.filename = "/home/blagus/src/PySonde/119fr.wav"
        self.sample_rate = 0
        self.bits = 0
        self.UDPport = 7355
        self.fskstream = []
        self.fsk_string = ""
        self.invert_phase = IntVar()
        self.n = 0
        self.prev_bit = 1
        self.cur_bit = 1
        self.frame = ""
        root.wm_title("PySonde %s" % version)
        w = Label(root, text="Sample rate: %d\nBits: %d" % (self.sample_rate, self.bits))
        #w.grid(row=0,column=2)
        self.button_pickFile = Button(frameControl,
            text="Select WAV",
            command=self.pick_file)
        self.button_pickFile.grid(row=0,column=0)

        self.button_processWAV = Button(frameControl,
            text="Process",
            command=self.processWAV)
        self.button_processWAV.grid(row=0,column=1)

        self.entry_UDPport = Label(frameControl,
            text="UDP port")
        #self.entry_UDPport.grid(row=1,column=0)

        self.button_processUDP = Button(frameControl,
            text="Process UDP",
            command=self.processUDP)
        self.button_processUDP.grid(row=1,column=0)

        self.button_stopUDP = Button(frameControl,
            text="Stop UDP",
            command=self.stopUDP,
            state="disabled")
        self.button_stopUDP.grid(row=1,column=1)

        self.checkbox_invert = Checkbutton(frameControl,
            text="Invert phase?",
            variable=self.invert_phase)
        self.checkbox_invert.grid(row=2, column=0)

        self.txtLog = ScrolledText(frameOutput,
            height=25,
            width=80)
        self.txtLog.grid(row=0,column=0)

    def pick_file(self):
        self.filename = filedialog.askopenfilename(initialdir = ".", title = "Select sonde *.wav recording", filetypes = (("WAV audio","*.wav"),("all files","*.*")))

    def processWAV(self):
        self.fsk_string = []
        self.txtLog.delete(1.0, END)
        self.n = 0
        self.baud = 4800 # hardcoded for RS41
        start = timer()
        framerate, waveFile = scipy.io.wavfile.read(self.filename)
        spb = framerate / self.baud
        try:
            if waveFile.shape[1] == 2:
                nchannels = 2
                waveFile = waveFile[:,0]
        except:
            waveFile = waveFile[:]
            nchannels = 1
        if waveFile.dtype == "uint8":
            waveFile = waveFile.astype("int8", copy=False)
        print("Load wav OK, get bits")
        pos = waveFile > 0
        npos = ~pos
        zc = ((pos[:-1] & npos[1:]) | (npos[:-1] & pos[1:])).nonzero()[0]
        inv = self.invert_phase.get()
        if inv == 0:
            waveFile[waveFile >= 0] = 1
            waveFile[waveFile < 0] = 0
        else:
            waveFile[waveFile >= 0] = 0
            waveFile[waveFile < 0] = 1
        print ( timer() - start )
        start = timer()
        prev = 1
        #cur = 1
        print(len(zc))
        lengths = [ ( (y-x) / spb ) for x,y in zip(zc,zc[1:])]
        #lengths.round()
        print(repr(lengths))
        print ( timer() - start )
        for i in zc:
            #prev = cur
            #cur = i
            #n = i-prev
            length = round((i-prev)/10)
            #length = int( ( (i-prev) / spb ) + 0.5 )
            if length > 0:
                self.fsk_string.extend([waveFile[i]] * length)
            prev = i
        #for cur,nxt in zip(zc, zc[1:]):
        #    n = nxt-cur
        #    length = int((n/self.spb) + 0.5)
        #    if length > 0:
        #        self.fsk_string.extend([waveFile[nxt]] * length)

        print("Get WAV OK!")


        self.txtLog.insert(END, ("Sample rate: %d Hz, channels: %d \n" % (framerate, nchannels)))
        self.txtLog.insert(END, ("Invert phase: %d \n" % self.invert_phase.get()))
        self.master.update()
        print("Search binary...")
        nxt = 0
        header = [0,0,0,0,1,0,0,0,0,1,1,0,1,1,0,1,0,1,0,1,0,0,1,1,1,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,0,1,1,0,1,0,0,1,0,1,0,0,1,0,0,0,0,0,0,1,1,1,1,1]
        indexes = []
        for i in range(len(self.fsk_string)):
            if self.UDP_active != True:
                if i < nxt:
                    continue
            if self.fsk_string[i:i+len(header)] == header:
                #print("found header")
                #indexes.append((i, i+320*8))
                if len(self.fsk_string[i:i+320*8]) == 320*8:
                    #print("Found at offset: %d" % i)
                    for bit in range(i, i+320*8):
                        self.frame += str(self.fsk_string[bit])
                    self.byte_frame = self.from_bits(self.frame)
                    self.get_frames()
                    self.frame = ""
                    if self.UDP_active == True:
                        self.fsk_string = []
                    else:
                        nxt = i + 320*8
        print("No more headers!")
        #self.decode_fsk()

    def processUDP(self):
        self.baud = 4800 # hardcoded for RS41
        self.spb = 48000 / self.baud
        self.fsk_string = []
        self.button_processUDP.config(state="disabled")
        self.button_stopUDP.config(state="normal")
        self.queue = queue.Queue()
        self.activeUDPthread = UDPthread(self.queue, self.UDPport)
        self.activeUDPthread.daemon = True
        self.activeUDPthread.start()
        self.UDP_active = True
        self.fskstream = []
        self.process_queue()

    def process_queue(self):
        start = timer()
        try:
            msg = numpy.fromstring(self.queue.get(), dtype="<h")
            if self.invert_phase.get() == 0:
                msg[msg >= 0] = 1
                msg[msg < 0] = 0
            else:
                msg[msg >= 0] = 0
                msg[msg < 0] = 1
            self.fskstream = msg
            self.decode_fsk()
            end = timer()
            #print(end-start)
            if self.UDP_active == True:
                #self.process_queue()
                self.master.after(1, self.process_queue)
            else:
                return 0
        except queue.Empty:
            if self.UDP_active == True:
                #self.process_queue()
                self.master.after(1, self.process_queue)
            else:
                return 0
        return 0

    def stopUDP(self):
        self.button_stopUDP.config(state="disabled")
        self.button_processUDP.config(state="normal")
        self.UDP_active = False
        self.lock = threading.Lock()
        self.lock.acquire()
        self.activeUDPthread.stop()

    def gps_time_process(self):
        gps_days = self.gps_week * 7 + (self.gps_time//86400)
        mjd = 44244 + gps_days
        J = mjd + 2468570
        C = 4 * J // 146097
        J = J - (146097 * C + 3) // 4
        Y = 4000 * (J + 1) // 1461001
        J = J - 1461 * Y // 4 + 31
        M = 80 * J // 2447
        self.gps_day = J - 2447 * M // 80
        J = M // 11
        self.gps_month = M + 2 - (12 * J)
        self.gps_year = 100 * (C - 49) + Y + J
        self.gps_time %= 86400
        self.gps_hours = self.gps_time/3600
        self.gps_minutes = (self.gps_time%3600) / 60
        self.gps_seconds = self.gps_time % 60

    #def gps_position(self):

    def get_frames(self):
        self.frame_num = self.byte_frame[0x3B] + (self.byte_frame[0x3C] << 8)
        self.sonde_serial = "" + chr(self.byte_frame[0x3D]) + chr(self.byte_frame[0x3E]) + chr(self.byte_frame[0x3F]) + chr(self.byte_frame[0x40]) + chr(self.byte_frame[0x41]) + chr(self.byte_frame[0x42]) + chr(self.byte_frame[0x43]) + chr(self.byte_frame[0x44])
        self.gps_week = self.byte_frame[0x95] + (self.byte_frame[0x96] << 8)
        self.gps_time = ( (self.byte_frame[0x9A] << 24) + (self.byte_frame[0x99] << 16) + (self.byte_frame[0x98] << 8) + self.byte_frame[0x97] ) // 1000
        self.gps_time_process()
        #self.gps_position =
        self.txtLog.insert(END, "[%5d] (%s) %04d-%02d-%02d %02d:%02d:%02d (W %04d) lat: lon: h: vH: d: vV: \n" % (self.frame_num, self.sonde_serial, self.gps_year, self.gps_month, self.gps_day, self.gps_hours, self.gps_minutes, self.gps_seconds, self.gps_week) )
        self.txtLog.see(END)
        #self.master.update()
        #frame = ""
        #start_offset = offset+(320*8)

    def from_bits(self, frame):
        xor_mask = [0x96, 0x83, 0x3E, 0x51, 0xB1, 0x49, 0x08, 0x98,
                    0x32, 0x05, 0x59, 0x0E, 0xF9, 0x44, 0xC6, 0x26,
                    0x21, 0x60, 0xC2, 0xEA, 0x79, 0x5D, 0x6D, 0xA1,
                    0x54, 0x69, 0x47, 0x0C, 0xDC, 0xE8, 0x5C, 0xF1,
                    0xF7, 0x76, 0x82, 0x7F, 0x07, 0x99, 0xA2, 0x2C,
                    0x93, 0x7C, 0x30, 0x63, 0xF5, 0x10, 0x2E, 0x61,
                    0xD0, 0xBC, 0xB4, 0xB6, 0x06, 0xAA, 0xF4, 0x23,
                    0x78, 0x6E, 0x3B, 0xAE, 0xBF, 0x7B, 0x4C, 0xC1]
        byte_frame = []
        for b in range(len(frame) // 8):
            byte = frame[(b+1)*8-1:(None if b*8 == 0 else b*8-1):-1]
            #self.txtLog.insert(END, "byte = %s\n" % (byte) )
            byte_frame.append( int(byte, 2) ^ xor_mask[b%64]  )
        return byte_frame

    #def decode_rs41(self):

    #    for i in range(len(self.fskstream)):


# UDP thread - separate
class UDPthread(threading.Thread):
    def __init__(self, queue, UDPport):
        threading.Thread.__init__(self)
        self.queue = queue
        #self.UDPport = 7355
        self.killme = None

    def stop(self):
        self.killme = True

    def run(self):
        UDP_IP = "127.0.0.1"
        UDP_PORT = 7355
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        while self.killme != True:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            self.queue.put(data)
root = Tk()
app = GUI(root)
root.mainloop()
