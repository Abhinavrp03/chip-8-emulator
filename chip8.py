import pygame
import random
import sys
import pickle
from typing import List, Tuple

class CHIP8:
    def __init__(self,scale=10):
        self.memory=[0]*0x1000
        self.V=[0]*16
        self.I=0
        self.PC=0x200
        self.stack=[]
        self.sp=0
        self.delay_timer=0
        self.sound_timer=0
        self.display=[[0]*64 for _ in range(32)]
        self.screen_width=64*scale
        self.screen_height=32*scale
        self.scale=scale
        pygame.init()
        self.screen=pygame.display.set_mode((self.screen_width,self.screen_height))
        pygame.display.set_caption("CHIP-8 Emulator")
        self.clock=pygame.time.Clock()
        self.keys=[0]*16
        self.key_mapping={pygame.K_1:0x1,pygame.K_2:0x2,pygame.K_3:0x3,pygame.K_4:0xC,pygame.K_q:0x4,pygame.K_w:0x5,pygame.K_e:0x6,pygame.K_r:0xD,pygame.K_a:0x7,pygame.K_s:0x8,pygame.K_d:0x9,pygame.K_f:0xE,pygame.K_z:0xA,pygame.K_x:0x0,pygame.K_c:0xB,pygame.K_v:0xF}
        self.fontset=[0xF0,0x90,0x90,0x90,0xF0,0x20,0x60,0x20,0x20,0x70,0xF0,0x10,0xF0,0x80,0xF0,0xF0,0x10,0xF0,0x10,0xF0,0x90,0x90,0xF0,0x10,0x10,0xF0,0x80,0xF0,0x10,0xF0,0xF0,0x80,0xF0,0x90,0xF0,0xF0,0x10,0x20,0x40,0x40,0xF0,0x90,0xF0,0x90,0xF0,0xF0,0x90,0xF0,0x10,0xF0,0xF0,0x90,0xF0,0x90,0x90,0xE0,0x90,0xE0,0x90,0xE0,0xF0,0x80,0x80,0x80,0xF0,0xE0,0x90,0x90,0x90,0xE0,0xF0,0x80,0xF0,0x80,0xF0,0xF0,0x80,0xF0,0x80,0x80]
        for i in range(len(self.fontset)):
            self.memory[i]=self.fontset[i]

    def load_binary(self,filepath):
        with open(filepath,"rb") as f:
            binary=f.read()
        for i,byte in enumerate(binary):
            self.memory[0x200+i]=byte

    def save_state(self,filepath):
        state={"memory":self.memory,"V":self.V,"I":self.I,"PC":self.PC,"stack":self.stack,"sp":self.sp,"delay_timer":self.delay_timer,"sound_timer":self.sound_timer,"display":self.display,"keys":self.keys}
        with open(filepath,"wb") as f:
            pickle.dump(state,f)

    def load_state(self,filepath):
        with open(filepath,"rb") as f:
            state=pickle.load(f)
        self.memory=state["memory"]
        self.V=state["V"]
        self.I=state["I"]
        self.PC=state["PC"]
        self.stack=state["stack"]
        self.sp=state["sp"]
        self.delay_timer=state["delay_timer"]
        self.sound_timer=state["sound_timer"]
        self.display=state["display"]
        self.keys=state["keys"]

    def emulate_cycle(self):
        if self.PC>=0x1000:
            return
        opcode=(self.memory[self.PC]<<8)|self.memory[self.PC+1]
        self.PC+=2
        self.execute_opcode(opcode)
        if self.delay_timer>0:
            self.delay_timer-=1
        if self.sound_timer>0:
            self.sound_timer-=1
            if self.sound_timer==1:
                print("Beep")

    def execute_opcode(self,opcode):
        x=(opcode&0x0F00)>>8
        y=(opcode&0x00F0)>>4
        n=opcode&0x000F
        nn=opcode&0x00FF
        nnn=opcode&0x0FFF
        if opcode==0x00E0:
            self.display=[[0]*64 for _ in range(32)]
        elif opcode==0x00EE:
            self.sp-=1
            self.PC=self.stack[self.sp]
        elif(opcode&0xF000)==0x1000:
            self.PC=nnn
        elif(opcode&0xF000)==0x2000:
            self.stack.append(self.PC)
            self.sp+=1
            self.PC=nnn
        elif(opcode&0xF000)==0x3000:
            if self.V[x]==nn:
                self.PC+=2
        elif(opcode&0xF000)==0x4000:
            if self.V[x]!=nn:
                self.PC+=2
        elif(opcode&0xF00F)==0x5000:
            if self.V[x]==self.V[y]:
                self.PC+=2
        elif(opcode&0xF000)==0x6000:
            self.V[x]=nn
        elif(opcode&0xF000)==0x7000:
            self.V[x]=(self.V[x]+nn)&0xFF
        elif(opcode&0xF000)==0xA000:
            self.I=nnn
        elif(opcode&0xF000)==0xD000:
            self.draw_sprite(x,y,n)
        elif(opcode&0xF0FF)==0xF007:
            self.V[x]=self.delay_timer
        elif(opcode&0xF0FF)==0xF015:
            self.delay_timer=self.V[x]
        elif(opcode&0xF0FF)==0xF018:
            self.sound_timer=self.V[x]
        elif(opcode&0xF0FF)==0xE09E:
            if self.keys[self.V[x]]:
                self.PC+=2
        elif(opcode&0xF0FF)==0xE0A1:
            if not self.keys[self.V[x]]:
                self.PC+=2
        elif(opcode&0xF0FF)==0xF00A:
            key_pressed=False
            for i in range(16):
                if self.keys[i]:
                    self.V[x]=i
                    key_pressed=True
                    break
            if not key_pressed:
                self.PC-=2
        elif(opcode&0xF0FF)==0xF029:
            self.I=self.V[x]*5
        elif(opcode&0xF0FF)==0xF033:
            self.memory[self.I]=self.V[x]//100
            self.memory[self.I+1]=(self.V[x]//10)%10
            self.memory[self.I+2]=self.V[x]%10
        elif(opcode&0xF0FF)==0xF055:
            for i in range(x+1):
                self.memory[self.I+i]=self.V[i]
        elif(opcode&0xF0FF)==0xF065:
            for i in range(x+1):
                self.V[i]=self.memory[self.I+i]
        else:
            print(f"Unknown opcode: {hex(opcode)}")

    def draw_sprite(self,x,y,height):
        self.V[0xF]=0
        x_coord=self.V[x]%64
        y_coord=self.V[y]%32
        for row in range(height):
            if y_coord+row>=32:
                break
            sprite_byte=self.memory[self.I+row]
            for col in range(8):
                if x_coord+col>=64:
                    break
                if(sprite_byte&(0x80>>col))!=0:
                    screen_x=x_coord+col
                    screen_y=y_coord+row
                    if self.display[screen_y][screen_x]==1:
                        self.V[0xF]=1
                    self.display[screen_y][screen_x]^=1

    def update_display(self):
        self.screen.fill((0,0,0))
        for y in range(32):
            for x in range(64):
                if self.display[y][x]==1:
                    pygame.draw.rect(self.screen,(255,255,255),(x*self.scale,y*self.scale,self.scale,self.scale))
        pygame.display.flip()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type==pygame.KEYDOWN:
                if event.key in self.key_mapping:
                    self.keys[self.key_mapping[event.key]]=1
                elif event.key==pygame.K_F5:
                    self.save_state("chip8_state.save")
                elif event.key==pygame.K_F8:
                    self.load_state("chip8_state.save")
            elif event.type==pygame.KEYUP:
                if event.key in self.key_mapping:
                    self.keys[self.key_mapping[event.key]]=0

    def run(self):
        if not any(self.memory[0x200:]):
            for y in range(16):
                for x in range(32):
                    if(x+y)%2==0:
                        self.display[y][x]=1
        while True:
            self.handle_input()
            self.emulate_cycle()
            self.update_display()
            self.clock.tick(60)

if __name__=="__main__":
    emulator=CHIP8(scale=10)
    emulator.load_binary("Logo.ch8")
    emulator.run()
