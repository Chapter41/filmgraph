"""
FilmGraph Controlled Vocabularies

Enums for cinematography terminology used across the film industry.
Each enum uses str+Enum for direct JSON serialization. AI-generated
values that don't match a known enum should use OTHER.
"""

from enum import Enum


class ShotSize(str, Enum):
    """How much of the subject fills the frame."""

    ECU = "ECU"          # Extreme Close-Up
    BCU = "BCU"          # Big Close-Up
    CU = "CU"            # Close-Up
    MCU = "MCU"          # Medium Close-Up
    MS = "MS"            # Medium Shot
    MLS = "MLS"          # Medium Long Shot
    MWS = "MWS"          # Medium Wide Shot (cowboy)
    WS = "WS"            # Wide Shot
    EWS = "EWS"          # Extreme Wide Shot
    INSERT = "INSERT"    # Insert / detail shot
    AERIAL = "AERIAL"    # Aerial overview
    OTHER = "OTHER"


class ShotType(str, Enum):
    """Compositional pattern of the shot."""

    SINGLE = "single"
    TWO_SHOT = "two-shot"
    GROUP = "group"
    OTS = "over-the-shoulder"
    POV = "point-of-view"
    REACTION = "reaction"
    ESTABLISHING = "establishing"
    INSERT = "insert"
    CUTAWAY = "cutaway"
    MASTER = "master"
    OTHER = "other"


class CameraMovement(str, Enum):
    """Physical or optical camera movement."""

    STATIC = "static"
    PAN = "pan"
    TILT = "tilt"
    DOLLY = "dolly"
    TRUCK = "truck"
    TRACKING = "tracking"
    HANDHELD = "handheld"
    CRANE = "crane"
    DRONE = "drone"
    ZOOM = "zoom"
    WHIP_PAN = "whip-pan"
    PUSH_IN = "push-in"
    PULL_OUT = "pull-out"
    ARC = "arc"
    RACK_FOCUS = "rack-focus"
    STEADICAM = "steadicam"
    OTHER = "other"


class CameraAngle(str, Enum):
    """Vertical angle of the camera relative to the subject."""

    EYE_LEVEL = "eye-level"
    HIGH = "high-angle"
    LOW = "low-angle"
    BIRD = "birds-eye"
    WORM = "worms-eye"
    DUTCH = "dutch-angle"
    OVERHEAD = "overhead"
    GROUND = "ground-level"
    OTHER = "other"


class Transition(str, Enum):
    """Editorial transition between shots."""

    CUT = "cut"
    DISSOLVE = "dissolve"
    FADE_IN = "fade-in"
    FADE_OUT = "fade-out"
    FADE_TO_BLACK = "fade-to-black"
    WIPE = "wipe"
    MATCH_CUT = "match-cut"
    JUMP_CUT = "jump-cut"
    J_CUT = "j-cut"
    L_CUT = "l-cut"
    SMASH_CUT = "smash-cut"
    OTHER = "other"
