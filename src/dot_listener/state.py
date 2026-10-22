"""Executable behavioral reference; not connected to microphone hardware."""
from dataclasses import dataclass
from enum import Enum

class Mode(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    SLEEP = "sleep"
    INTERRUPTED = "interrupted"

@dataclass
class CaptureState:
    mode: Mode = Mode.IDLE
    consent: bool = False
    microphone_granted: bool = False
    interruption_count: int = 0

    @property
    def microphone_open(self): return self.mode == Mode.RECORDING

    def apply(self, action: str, visible_user_action=False):
        if action == "start":
            if not (self.consent and self.microphone_granted and visible_user_action):
                raise ValueError("Visible user action, consent and permission are required")
            if self.mode == Mode.SLEEP: raise ValueError("Wake explicitly before starting")
            self.mode = Mode.RECORDING
        elif action == "pause":
            if self.mode != Mode.SLEEP: self.mode = Mode.PAUSED
        elif action == "sleep": self.mode = Mode.SLEEP
        elif action == "wake":
            if not visible_user_action: raise ValueError("No automatic microphone restart")
            self.mode = Mode.IDLE
        elif action == "interrupt":
            if self.mode == Mode.RECORDING:
                self.interruption_count += 1
                self.mode = Mode.INTERRUPTED
        elif action == "revoke":
            self.microphone_granted = False
            self.mode = Mode.IDLE
        else: raise ValueError("Unknown action")
        return self.mode

@dataclass(frozen=True)
class SleepWindow:
    start_minute: int
    end_minute: int
    def __post_init__(self):
        if not (0 <= self.start_minute < 1440 and 0 <= self.end_minute < 1440):
            raise ValueError("Minutes must be in [0, 1440)")
        if self.start_minute == self.end_minute: raise ValueError("Ambiguous full-day window")
    def contains(self, minute: int):
        if not 0 <= minute < 1440: raise ValueError("Invalid minute")
        if self.start_minute < self.end_minute:
            return self.start_minute <= minute < self.end_minute
        return minute >= self.start_minute or minute < self.end_minute
