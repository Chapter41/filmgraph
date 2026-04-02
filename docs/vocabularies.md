# Controlled Vocabularies

FilmGraph uses `str` enums for all categorical cinematography fields. Each enum includes an `OTHER` fallback for values that don't fit the taxonomy.

## ShotSize

How much of the subject fills the frame.

| Value | Name | Description |
|-------|------|-------------|
| `ECU` | Extreme Close-Up | Eyes, mouth, or single detail |
| `BCU` | Big Close-Up | Full face, tight framing |
| `CU` | Close-Up | Head and shoulders |
| `MCU` | Medium Close-Up | Chest up |
| `MS` | Medium Shot | Waist up |
| `MLS` | Medium Long Shot | Knees up |
| `MWS` | Medium Wide Shot | Full body with some environment (cowboy shot) |
| `WS` | Wide Shot | Full body, environment visible |
| `EWS` | Extreme Wide Shot | Landscape, establishing |
| `INSERT` | Insert / Detail | Object detail, not a person |
| `AERIAL` | Aerial | Drone or helicopter overview |
| `OTHER` | Other | Doesn't fit above categories |

## ShotType

Compositional pattern of the shot.

| Value | Description |
|-------|-------------|
| `single` | One person |
| `two-shot` | Two people |
| `group` | Three or more |
| `over-the-shoulder` | Camera behind one person looking at another |
| `point-of-view` | Camera represents a character's view |
| `reaction` | Character reacting to off-screen action |
| `establishing` | Sets the scene location/time |
| `insert` | Detail or cutaway object |
| `cutaway` | Brief shot away from main action |
| `master` | Wide coverage of entire scene |
| `other` | Doesn't fit above categories |

## CameraMovement

Physical or optical camera movement.

| Value | Description |
|-------|-------------|
| `static` | Locked-off, no movement |
| `pan` | Horizontal rotation on axis |
| `tilt` | Vertical rotation on axis |
| `dolly` | Camera moves forward/backward on track |
| `truck` | Camera moves laterally |
| `tracking` | Camera follows subject |
| `handheld` | Operator-held, intentional instability |
| `crane` | Vertical lift on crane/jib |
| `drone` | Unmanned aerial movement |
| `zoom` | Optical zoom (not physical movement) |
| `whip-pan` | Very fast pan creating motion blur |
| `push-in` | Slow dolly toward subject |
| `pull-out` | Slow dolly away from subject |
| `arc` | Camera moves in an arc around subject |
| `rack-focus` | Focus shift between planes |
| `steadicam` | Stabilized handheld movement |
| `other` | Doesn't fit above categories |

## CameraAngle

Vertical angle of the camera relative to the subject.

| Value | Description |
|-------|-------------|
| `eye-level` | Camera at subject's eye height |
| `high-angle` | Camera above, looking down |
| `low-angle` | Camera below, looking up |
| `birds-eye` | Directly above |
| `worms-eye` | Directly below |
| `dutch-angle` | Camera tilted on roll axis |
| `overhead` | Above but not directly vertical |
| `ground-level` | Camera on the ground |
| `other` | Doesn't fit above categories |

## Transition

Editorial transition between shots.

| Value | Description |
|-------|-------------|
| `cut` | Instantaneous change |
| `dissolve` | Gradual blend between shots |
| `fade-in` | From black/color to image |
| `fade-out` | From image to black/color |
| `fade-to-black` | Specific fade to black |
| `wipe` | Geometric transition |
| `match-cut` | Cut matched by visual/audio similarity |
| `jump-cut` | Discontinuous cut within same scene |
| `j-cut` | Audio from next shot starts before visual cut |
| `l-cut` | Audio from previous shot continues after visual cut |
| `smash-cut` | Abrupt, jarring transition for effect |
| `other` | Doesn't fit above categories |
