#!/usr/bin/env python2
import random, math, time
import pygame
import pygame.midi
from nodes import *

class Midi:

  channel = 3

  def __init__(self):
    pygame.midi.init() 
    self.inp = pygame.midi.Input(3)
    self.out = pygame.midi.Output(4)

  def note_on(self,note):
    if note: self.out.note_on(note[0],note[1],self.channel-1)

  def note_off(self,note):
    if note: self.out.note_off(note,0,self.channel-1)

  def quit(self):
    del self.inp
    del self.out
    pygame.midi.quit()

class Recorder:

  def __init__(self,length):
    self.length = length
    self.sequence = [None]*length
    self.playing = {}

  def note_on(self,step,note,vel):
    self.playing[note] = [step,vel]

  def note_off(self,step,note):
    # find note on
    dur = step - self.playing[note][0]
    
    if dur < 0: dur = self.length + dur
    elif dur > self.length: dur = self.length
    if dur != 0:
      vel = self.playing[note][1]
      # insert into sequence
      self.sequence[step] = [note,vel,dur]
    del self.playing[note]

class Player:

  def __init__(self,length):
    self.length = length
    self.sequence = [None]*length
    self.note_ons = [None]*length
    self.note_offs = [None]*length

  def copy(self,sequence):
    self.length = len(sequence)
    self.sequence = sequence
    self.update_notes()

  def update_notes(self):
    self.note_ons = [None]*self.length
    self.note_offs = [None]*self.length
    for i in range(self.length):
      if self.sequence[i]:
        self.note_ons[i] = [self.sequence[i][0],self.sequence[i][1]]
        dur = self.sequence[i][2]
        off = (i + dur)%self.length
        self.note_offs[off] = self.sequence[i][0]

class Looper:

  length = 32 # 16th

  def __init__(self,midi):
    self.ticks = 0
    self.step = 0
    self.midi = midi
    self.recorder = Recorder(self.length)
    self.player = Player(self.length)
    self.running = False

  def run(self):

    if self.midi.inp.poll():
      event = midi.inp.read(1)[0][0]
      # http://www.midi.org/techspecs/midimessages.php
      if event[0] == 250: # start
        self.ticks = 0
        self.step = 0
        self.running = True
      elif event[0] == 251: # continue
        self.running = True
      elif event[0] == 252: # stop
        self.running = False
        # TODO: all notes off
        midi.out.write_short(0xB2,123,0)
      elif self.running: 
        if event[0] == 248: # clock
          self.ticks = (self.ticks + 1) % 6
          if ((self.ticks % 6) == 0): # 16th
            #self.recorder.sequence[self.step] = None
            midi.note_off(self.player.note_offs[self.step])
            midi.note_on(self.player.note_ons[self.step])
            self.step = (self.step + 1) % self.length
        elif event[0] == 143+self.midi.channel: # note on
          if event[2] == 0: # mpc sends vol 0 instead of note off
            self.recorder.note_off(self.step,event[1])
          else:
            self.recorder.note_on(self.step,event[1],event[2])
        elif event[0] == 127+self.midi.channel: # note off
          self.recorder.note_off(self.step,event[1])
        elif event[0] == 194:
          self.player.copy(self.recorder.sequence)
          print "seq"
          print self.player.sequence
          print "ons"
          print self.player.note_ons
          print "offs"
          print self.player.note_offs
        #elif event[0] == 175+self.midi.channel: # cc
        # TODO: Aftertouch
        #else:
          #print event

midi = Midi()
looper = Looper(midi)

while True:
  looper.run()

midi.quit()
