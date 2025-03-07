import pygame
import random
import sys
import pickle

class Chip8:
    def __init__(self):
        pygame.init()
        self.memory = [0] * 4096
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200
        self.stack = []
        self.delay_timer = 0
        self.sound_timer = 0
        self.screen_width = 64
        self.screen_height = 32
        self.pixel_size = 10
        self.display = pygame.display.set_mode((self.screen_width * self.pixel_size, self.screen_height * self.pixel_size))
        pygame.display.set_caption("CHIP-8 Emulator")
        self.gfx = [[0 for _ in range(self.screen_width)] for _ in range(self.screen_height)]
        self.key_map = {pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC, pygame.K_q: 0x4, pygame.K_w: 0x5, 
                        pygame.K_e: 0x6, pygame.K_r: 0xD, pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE, 
                        pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF}
        self.keys = [0] * 16
        self.fontset = [0xF0, 0x90, 0x90, 0x90, 0xF0, 0x20, 0x60, 0x20, 0x20, 0x70, 0xF0, 0x10, 0xF0, 0x80, 0xF0, 0xF0, 0x10, 0xF0, 
                        0x10, 0xF0, 0x90, 0x90, 0xF0, 0x10, 0x10, 0xF0, 0x80, 0xF0, 0x10, 0xF0, 0xF0, 0x80, 0xF0, 0x90, 0xF0, 0xF0, 
                        0x10, 0x20, 0x40, 0x40, 0xF0, 0x90, 0xF0, 0x90, 0xF0, 0xF0, 0x90, 0xF0, 0x10, 0xF0, 0xF0, 0x90, 0xF0, 0x90,
                          0x90, 0xE0, 0x90, 0xE0, 0x90, 0xE0, 0xF0, 0x80, 0x80, 0x80, 0xF0, 0xE0, 0x90, 0x90, 0x90, 0xE0, 0xF0, 0x80, 
                          0xF0, 0x80, 0xF0, 0xF0, 0x80, 0xF0, 0x80, 0x80]
        for i, byte in enumerate(self.fontset):
            self.memory[i] = byte
            
    def loadgamefile(self, filename):
        with open(filename, 'rb') as f:
            rom = f.read()
            for i, byte in enumerate(rom):
                self.memory[0x200 + i] = byte
                
    def emulate_cycle(self):
        opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
        self.pc += 2
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        nnn = opcode & 0x0FFF
        kk = opcode & 0x00FF
        n = opcode & 0x000F
        if opcode == 0x00E0:
            self.gfx = [[0 for _ in range(self.screen_width)] for _ in range(self.screen_height)]
        elif opcode == 0x00EE:
            self.pc = self.stack.pop()
        elif opcode & 0xF000 == 0x1000:
            self.pc = nnn
        elif opcode & 0xF000 == 0x2000:
            self.stack.append(self.pc)
            self.pc = nnn
        elif opcode & 0xF000 == 0x3000:
            if self.V[x] == kk:
                self.pc += 2
        elif opcode & 0xF000 == 0x4000:
            if self.V[x] != kk:
                self.pc += 2
        elif opcode & 0xF00F == 0x5000:
            if self.V[x] == self.V[y]:
                self.pc += 2
        elif opcode & 0xF000 == 0x6000:
            self.V[x] = kk
        elif opcode & 0xF000 == 0x7000:
            self.V[x] = (self.V[x] + kk) & 0xFF
        elif opcode & 0xF00F == 0x8000:
            self.V[x] = self.V[y]
        elif opcode & 0xF00F == 0x8001:
            self.V[x] |= self.V[y]
        elif opcode & 0xF00F == 0x8002:
            self.V[x] &= self.V[y]
        elif opcode & 0xF00F == 0x8003:
            self.V[x] ^= self.V[y]
        elif opcode & 0xF00F == 0x8004:
            self.V[x] = (self.V[x] + self.V[y]) & 0xFF
            self.V[0xF] = 1 if self.V[x] + self.V[y] > 255 else 0
        elif opcode & 0xF00F == 0x8005:
            self.V[0xF] = 1 if self.V[x] > self.V[y] else 0
            self.V[x] = (self.V[x] - self.V[y]) & 0xFF
        elif opcode & 0xF00F == 0x8006:
            self.V[0xF] = self.V[x] & 0x1
            self.V[x] >>= 1
        elif opcode & 0xF00F == 0x8007:
            self.V[0xF] = 1 if self.V[y] > self.V[x] else 0
            self.V[x] = (self.V[y] - self.V[x]) & 0xFF
        elif opcode & 0xF00F == 0x800E:
            self.V[0xF] = (self.V[x] >> 7) & 0x1
            self.V[x] = (self.V[x] << 1) & 0xFF
        elif opcode & 0xF00F == 0x9000:
            if self.V[x] != self.V[y]:
                self.pc += 2
        elif opcode & 0xF000 == 0xA000:
            self.I = nnn
        elif opcode & 0xF000 == 0xB000:
            self.pc = nnn + self.V[0]
        elif opcode & 0xF000 == 0xC000:
            self.V[x] = random.randint(0, 255) & kk
        elif opcode & 0xF000 == 0xD000:
            self.V[0xF] = 0
            for row in range(n):
                sprite_byte = self.memory[self.I + row]
                for col in range(8):
                    if sprite_byte & (0x80 >> col):
                        x_pos = (self.V[x] + col) % self.screen_width
                        y_pos = (self.V[y] + row) % self.screen_height
                        if self.gfx[y_pos][x_pos] == 1:
                            self.V[0xF] = 1
                        self.gfx[y_pos][x_pos] ^= 1
        elif opcode & 0xF0FF == 0xE09E:
            if self.keys[self.V[x]]:
                self.pc += 2
        elif opcode & 0xF0FF == 0xE0A1:
            if not self.keys[self.V[x]]:
                self.pc += 2
        elif opcode & 0xF0FF == 0xF007:
            self.V[x] = self.delay_timer
        elif opcode & 0xF0FF == 0xF00A:
            pressed = False
            for i, key in enumerate(self.keys):
                if key:
                    self.V[x] = i
                    pressed = True
            if not pressed:
                self.pc -= 2
        elif opcode & 0xF0FF == 0xF015:
            self.delay_timer = self.V[x]
        elif opcode & 0xF0FF == 0xF018:
            self.sound_timer = self.V[x]
        elif opcode & 0xF0FF == 0xF01E:
            self.I = (self.I + self.V[x]) & 0xFFF
        elif opcode & 0xF0FF == 0xF029:
            self.I = self.V[x] * 5
        elif opcode & 0xF0FF == 0xF033:
            self.memory[self.I] = self.V[x] // 100
            self.memory[self.I + 1] = (self.V[x] // 10) % 10
            self.memory[self.I + 2] = self.V[x] % 10
        elif opcode & 0xF0FF == 0xF055:
            for i in range(x + 1):
                self.memory[self.I + i] = self.V[i]
        elif opcode & 0xF0FF == 0xF065:
            for i in range(x + 1):
                self.V[i] = self.memory[self.I + i]
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
            
    def todrawgraphics(self):
        self.display.fill((0, 0, 0))
        for y in range(self.screen_height):
            for x in range(self.screen_width):
                if self.gfx[y][x] == 1:
                    pygame.draw.rect(self.display, (255, 255, 255), (x * self.pixel_size, y * self.pixel_size, self.pixel_size, 
                                                                     self.pixel_size))
        pygame.display.flip()

    def save(self, filename="chip8.pkl"):
        state = {
            'memory': self.memory,
            'V': self.V,
            'I': self.I,
            'pc': self.pc,
            'stack': self.stack,
            'delay_timer': self.delay_timer,
            'sound_timer': self.sound_timer,
            'gfx': self.gfx,
            'keys': self.keys
        }
        with open(filename, 'wb') as f:
            pickle.dump(state, f)
        print(f"State saved to {filename}")

    def load(self, filename="chip8.pkl"):
        try:
            with open(filename, 'rb') as f:
                state = pickle.load(f)
                self.memory = state['memory']
                self.V = state['V']
                self.I = state['I']
                self.pc = state['pc']
                self.stack = state['stack']
                self.delay_timer = state['delay_timer']
                self.sound_timer = state['sound_timer']
                self.gfx = state['gfx']
                self.keys = state['keys']
            print(f"State loaded from {filename}")
        except FileNotFoundError:
            print(f"Save file {filename} not found!")
        except Exception as e:
            print(f"Error loading state: {e}")

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in self.key_map:
                    self.keys[self.key_map[event.key]] = 1
                elif event.key == pygame.K_F5:
                    self.save_state()
                elif event.key == pygame.K_F6:
                    self.load_state()
            elif event.type == pygame.KEYUP:
                if event.key in self.key_map:
                    self.keys[self.key_map[event.key]] = 0
                    
    def main_loop(self):
        self.loadgamefile("Tetris.ch8")
        clock = pygame.time.Clock()
        while True:
            self.handle_input()
            self.emulate_cycle()
            self.todrawgraphics()
            clock.tick(60)
            
if __name__ == "__main__":
    emulator = Chip8()
    emulator.main_loop()
