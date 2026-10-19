"""Authenticated native datagrams. TLS issues separate per-direction session keys."""
import struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

HEADER = struct.Struct('!4s16sQ')
MAGIC = b'PPU1'
MAX_PAYLOAD = 8192

class Cipher:
    def __init__(self, session, key):
        self.session = session
        self.aes = AESGCM(key)
        self.sequence = 0
        self.highest = -1
        self.seen = 0

    def encode(self, payload):
        if len(payload) > MAX_PAYLOAD: raise ValueError('Oversized datagram')
        if self.sequence >= 2**64: raise ValueError('Session exhausted')
        seq = self.sequence
        self.sequence += 1
        header = HEADER.pack(MAGIC, self.session, seq)
        return header + self.aes.encrypt(b'\0'*4 + seq.to_bytes(8, 'big'), payload, header)

    def decode(self, packet):
        if not HEADER.size + 16 <= len(packet) <= HEADER.size + 16 + MAX_PAYLOAD: return None
        magic, session, seq = HEADER.unpack_from(packet)
        if magic != MAGIC or session != self.session: return None
        delta = self.highest - seq
        if delta >= 256 or (delta >= 0 and self.seen & (1 << delta)): return None
        try:
            payload = self.aes.decrypt(b'\0'*4 + seq.to_bytes(8, 'big'), packet[HEADER.size:], packet[:HEADER.size])
        except InvalidTag: return None
        if seq > self.highest:
            shift = seq - self.highest
            self.seen = 0 if shift >= 256 else (self.seen << shift) & ((1 << 256)-1)
            self.highest = seq
            self.seen |= 1
        else: self.seen |= 1 << delta
        return payload
