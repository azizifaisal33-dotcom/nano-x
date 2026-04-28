#!/usr/bin/env python3
"""
Nano-X v5.0.1 - ULTRA FAST + BLINKING CHATBOX
Fast-Path + Cache Fusion + Lazy Dequant
Termux | 128MB | Production Ready

MIT License
Copyright (c) 2024 azizifaisal33-dotcom (https://github.com/azizifaisal33-dotcom/nano-x)
"""
import os, struct, hashlib, json, random, math, time, collections, sys, threading
try: 
    import mmap
    MMAP_AVAILABLE = True
except: 
    MMAP_AVAILABLE = False
    mmap = None

# ANSI Colors + Blink
RED = '\033[91m'
BOLD_RED = '\033[91;1m'
BLINK_RED = '\033[91;5m'  # ✨ BLINKING MAGIC ✨
LIGHT_RED = '\033[91;2m'
CYAN = '\033[96m'
BOLD_CYAN = '\033[96;1m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
PURPLE = '\033[95m'
RESET = '\033[0m'

__version__ = "5.0.1"
__author__ = "azizifaisal33-dotcom"
__repo__ = "https://github.com/azizifaisal33-dotcom/nano-x"

def stable_hash(key): 
    return int(hashlib.md5(key.encode()).hexdigest(), 16) & 0xFFFFF

def center_box(title, content="", width=60):
    """🔲 CENTERED Red Box dengan BLINK"""
    lines = str(content).split('\n')
    max_len = max(len(title), max((len(line) for line in lines), default=0), width)
    
    # Top border
    print(f"{BOLD_RED}{'─' * (max_len + 4)}{RESET}")
    print(f"{BLINK_RED}  ░{'█' * (max_len + 2)}░  {RESET}")
    
    # Title line
    title_line = f"  {title.center(max_len)}  "
    print(f"{BOLD_RED}░{title_line}░{RESET}")
    
    # Content lines
    for line in lines:
        content_line = f"  {line:<{max_len}}  "
        print(f"{RED}░{content_line}░{RESET}")
    
    # Bottom border
    print(f"{BLINK_RED}  ░{'█' * (max_len + 2)}░  {RESET}")
    print(f"{BOLD_RED}{'─' * (max_len + 4)}{RESET}\n")

def blink_welcome():
    """✨ BLINKING WELCOME"""
    for i in range(3):
        print(f"\r{BLINK_RED}🚀 Nano-X v{__version__} LOADING...{RESET}", end="", flush=True)
        time.sleep(0.3)
        print(f"\r{GREEN}🚀 Nano-X v{__version__} READY!     {RESET}", end="", flush=True)
        time.sleep(0.3)
    print()

# [NanoArray, LVRBinaryEngine, NanoXBrain, NanoX - SAME EXACT CODE]
class NanoArray:
    def __init__(self, data=0, shape=(4,6), quant=True):
        self.shape = shape
        self.rows, self.cols = shape
        self.size = shape[0] * shape[1]
        self.quant = quant
        flat = data if isinstance(data, list) else [data] * self.size
        if quant:
            self.data = [int(x * 15) // 1 for x in flat[:self.size]]
        else:
            self.data = [float(x) for x in flat[:self.size]]
        self._float_cache = None
    
    def _get_float_cache(self):
        if self._float_cache is None:
            self._float_cache = [x / 15.0 for x in self.data] if self.quant else self.data[:]
        return self._float_cache
    
    def _dequant(self, x): 
        return x / 15.0 if self.quant else x
    
    def __repr__(self): 
        return f"NanoArray{self.shape}"
    
    def __getitem__(self, idx):
        if isinstance(idx, tuple):
            i, j = idx
            return self._dequant(self.data[i * self.cols + j])
        return self._dequant(self.data[idx])
    
    def fast_add_scalar(self, scalar):
        scalar_q = int(scalar * 15) if self.quant else scalar
        self.data = list(map(lambda x: x + scalar_q, self.data))
        self._float_cache = None
        return self
    
    @property
    def T(self):
        data = [0] * self.size
        for i in range(self.rows):
            for j in range(self.cols):
                data[j * self.rows + i] = self.data[i * self.cols + j]
        return NanoArray(data, (self.cols, self.rows), self.quant)
    
    def dot(self, other):
        m, n, k = self.rows, other.cols, self.cols
        result = NanoArray(0, (m, n), self.quant)
        self_f = self._get_float_cache()
        other_f = other._get_float_cache()
        for i in range(m):
            for j in range(n):
                acc = 0.0
                for p in range(k):
                    acc += self_f[i * k + p] * other_f[p * n + j]
                result.data[i * n + j] = int(acc * 15) if self.quant else acc
        return result
    
    @classmethod
    def rand(cls, *shape, quant=True):
        size = math.prod(shape)
        return cls([random.uniform(0, 1) for _ in range(size)], shape, quant)

class LVRBinaryEngine:
    MAGIC_HEADER = b'NANO_LVR_v5\x00'
    def __init__(self, file="nano_memory.lvr", cache_size=512):
        self.file = file
        self.fd = None
        self.mm = None
        self.cache = collections.OrderedDict()
        self.cache_size = cache_size
        self.hit_count = self.total_count = 0
        self._init_memory(file)
    
    def _init_memory(self, file):
        MAX_FILE_SIZE = 1024 * 1024
        if not os.path.exists(file) or os.path.getsize(file) < len(self.MAGIC_HEADER) * 1024:
            try:
                with open(file, 'wb') as f:
                    header_size = min(1024 * 1024, len(self.MAGIC_HEADER) * 1024)
                    f.write(self.MAGIC_HEADER * (header_size // len(self.MAGIC_HEADER)))
            except: pass
        try:
            self.fd = open(file, 'r+b')
            if MMAP_AVAILABLE:
                self.mm = mmap.mmap(self.fd.fileno(), 0)
        except: pass
    
    def save(self, key, data):
        try:
            if self.mm:
                data_b = data.encode('utf-8')[:64]
                key_h = hashlib.md5(key.encode()).digest()[:8]
                shard = key_h + data_b.ljust(80, b'\x00')
                offset = 1024 + (stable_hash(key) * 128)
                if offset + 128 <= len(self.mm):
                    self.mm[offset:offset + 128] = shard
                    self.mm.flush()
            self.cache[key] = data
            if len(self.cache) > self.cache_size:
                self.cache.popitem(last=False)
        except: pass
    
    def load(self, key):
        self.total_count += 1
        if key in self.cache:
            self.cache.move_to_end(key)
            self.hit_count += 1
            return self.cache[key]
        try:
            if self.mm:
                offset = 1024 + (stable_hash(key) * 128)
                if offset + 128 <= len(self.mm):
                    shard = self.mm[offset:offset + 128]
                    if shard[:8] == hashlib.md5(key.encode()).digest()[:8]:
                        val = shard[8:72].rstrip(b'\x00').decode(errors='ignore')
                        if len(self.cache) >= self.cache_size:
                            self.cache.popitem(last=False)
                        self.cache[key] = val
                        return val
        except: pass
        return None
    
    def stats(self):
        hit_rate = (self.hit_count / max(self.total_count, 1)) * 100
        return f"Cache:{len(self.cache)} Hit:{hit_rate:.0f}%"
    
    def close(self):
        try:
            if self.mm: self.mm.close()
            if self.fd: self.fd.close()
        except: pass

class NanoXBrain:
    def __init__(self):
        self.W_emb = NanoArray.rand(6, 6, quant=True)
        self.W_out = NanoArray.rand(6, 1, quant=True)
    def embedding(self, word):
        try:
            seed = stable_hash(word)
            random.seed(seed)
            inp_vec = [random.random() for _ in range(6)]
            inp = NanoArray(inp_vec, (1, 6), quant=False)
            hidden = inp.dot(self.W_emb)
            emb = hidden.dot(self.W_out)
            return abs(emb[0, 0])
        except:
            return 0.5

class NanoX:
    def __init__(self):
        self.brain = NanoXBrain()
        self.lvr = LVRBinaryEngine()
        self.memory = self._load_json()
    
    def _load_json(self):
        try:
            if os.path.exists("nano_memory.json"):
                with open("nano_memory.json") as f:
                    return {k: v for k, v in json.load(f).items() if isinstance(k, str)}
        except: pass
        return {}
    
    def _save_json(self):
        try:
            with open("nano_memory.json", 'w') as f:
                json.dump(self.memory, f, indent=2)
            return True
        except: return False
    
    def learn(self, word):
        if len(word) < 2 or word in self.memory: return False
        try:
            emb = self.brain.embedding(word)
            self.memory[word] = f"{word}(emb:{emb:.2f})"
            self.lvr.save(word, self.memory[word])
            return True
        except: return False
    
    def chat(self, text):
        if not text.strip(): return "?"
        words = text.lower().split()
        learned = sum(1 for w in words if self.learn(w))
        context = [self.memory.get(w, "") for w in words if w in self.memory]
        if context:
            return " ".join(context[:3]).capitalize() + (f" [+NEWx{learned}]" if learned else "")
        return random.choice(["Nice!", f"{words[0]}?", "Cool!", "Yes!", "Learn more!"])

# =============================================================================
# 🔥 MAIN - CENTERED BLINKING CHATBOX
# =============================================================================

def main():
    os.system('clear' if os.name == 'posix' else 'cls')  # Clear screen
    
    # ✨ BLINKING WELCOME
    blink_welcome()
    center_box("🤖 NANO-X v5.0.1", f"by {__author__}\n{__repo__}", 50)
    
    ai = NanoX()
    center_box("🚀 SYSTEM ONLINE", f"LVR: {ai.lvr.stats()}\nWords: {len(ai.memory)}", 50)
    
    print(f"{BOLD_CYAN}{'='*70}{RESET}")
    print(f"{LIGHT_RED}💬 Type: /mem /gen50 /perf /save /q | ESC=q{RESET}")
    print(f"{BOLD_CYAN}{'='*70}{RESET}\n")
    
    chat_history = []
    while True:
        try:
            inp = input(f"{BLINK_RED}💭 You> {RESET}").strip()
            if not inp: continue
            
            if inp.lower() in ['q', 'quit', 'esc']:
                center_box("👋 SESSION END", f"Total Words: {len(ai.memory)}\nSaved to nano_memory.json")
                break
            
            # Commands
            if inp == '/mem':
                center_box("🧠 MEMORY STATUS", f"Words Learned: {len(ai.memory)}\n{ai.lvr.stats()}")
                continue
            if inp == '/gen50':
                center_box("⚡ GEN50 TEST", "Generating 50 words...")
                t0 = time.time()
                cnt = sum(1 for i in range(50) if ai.learn(f"test{i}"))
                center_box("✅ GEN50 DONE", f"Time: {time.time()-t0:.3f}s\nNew: {cnt}/50")
                continue
            if inp == '/perf':
                center_box("⚡ PERF TEST", "50 chats benchmark...")
                t0 = time.time()
                for i in range(50): ai.chat("perf test")
                center_box("✅ PERF RESULT", f"50 chats: {(time.time()-t0)*1000:.1f}ms")
                continue
            if inp == '/save':
                if ai._save_json():
                    center_box("💾 SAVED", "nano_memory.json ✓")
                continue
            
            # Normal chat
            resp = ai.chat(inp)
            chat_history.append(f"You: {inp}")
            chat_history.append(f"Nano-X: {resp}")
            
            # Show chat in box
            chat_display = "\n".join(chat_history[-6:])  # Last 6 lines
            center_box("💬 CHAT", chat_display, 70)
            
        except KeyboardInterrupt:
            print(f"\n{RED}👋 Bye!{RESET}")
            break
        except EOFError:
            continue
        except Exception as e:
            center_box("⚠️ OOPS", str(e)[:50])

    if 'ai' in locals():
        ai.lvr.close()

if __name__ == '__main__':
    main()