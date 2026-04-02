# Schema Reference

FilmGraph uses a strict hierarchy: **FilmGraph → Scene → Shot**, with each shot containing typed layers.

## Hierarchy

```
FilmGraph
├── schema_version: str        # "filmgraph/v1"
├── meta: FilmMeta
│   ├── title: str
│   ├── original_title?: str
│   ├── year?: int
│   ├── duration: float        # seconds
│   ├── frame_rate?: float
│   ├── resolution?: str       # "1920x1080"
│   ├── language?: str
│   └── sources: [DataSource]
├── entities: Entities
│   ├── characters: [Character]
│   └── locations: [Location]
├── scenes: [Scene]
│   ├── id: int
│   ├── title: str
│   ├── summary: str
│   ├── start_time / end_time: float
│   ├── location?: str
│   ├── characters: [str]      # character IDs
│   ├── mood?: str
│   ├── themes: [str]
│   ├── shots: [Shot]          # see below
│   └── dialogue: [DialogueLine]
└── events: [Event]
    ├── id: str
    ├── name: str
    ├── description: str
    ├── timestamp: float
    └── scene_id?: int
```

## Shot

The atomic unit — everything between two cuts.

```
Shot
├── id: str
├── order: int
├── start_time / end_time: float
├── timecode_in / timecode_out?: str    # SMPTE "01:23:45:12"
├── duration: float                     # computed
│
├── cinematography: Cinematography
│   ├── shot_size?: ShotSize
│   ├── shot_type?: ShotType
│   ├── camera_angle?: CameraAngle
│   ├── camera_movement?: CameraMovement
│   ├── lens?: str
│   ├── depth_of_field?: str
│   ├── composition: [str]
│   └── notes?: str
│
├── visual: Visual
│   ├── description?: str
│   ├── dominant_colors: [str]
│   ├── lighting?: str
│   └── visual_style?: str
│
├── audio: Audio
│   ├── dialogue: [DialogueLine]
│   │   ├── speaker?: str              # character ID
│   │   ├── text: str
│   │   ├── start_time / end_time: float
│   │   ├── language?: str
│   │   └── words: [{word, start, end, confidence}]
│   ├── sound?: str
│   └── music_cues: [MusicCue]
│       ├── label: str
│       ├── start_time / end_time?: float
│       └── type?: str                 # "score", "diegetic", "sfx", "ambient"
│
├── editorial: Editorial
│   ├── transition_in / transition_out?: Transition
│   ├── source_clip?: str
│   ├── thumbnail_path?: str
│   └── confidence?: float
│
├── characters_visible: [str]          # character IDs
├── emotional_tone?: str
├── source?: str                       # "ccsl", "pipeline", "manual"
├── verified?: bool
└── custom: dict                       # escape hatch
```

## Design Principles

1. **Layers are independent.** Each shot layer (cinematography, visual, audio, editorial) can be populated by a different tool. A CCSL fills cinematography, an SRT fills audio, a vision model fills visual.

2. **Everything is optional except time.** A shot must have `id`, `order`, `start_time`, `end_time`. Everything else can be `None` or empty.

3. **IDs are slugs.** Characters and locations use slug-format IDs (`john-smith`, `berlin-cafe`) and are referenced by ID from shots and scenes.

4. **`custom` is the escape hatch.** Any domain-specific metadata goes into `custom: dict` rather than polluting the core schema.

5. **`OTHER` is always valid.** Every controlled vocabulary enum includes an `OTHER` value for edge cases that don't fit the taxonomy.
