# IGVC Dynamic AutoNav Course — Agent Handoff Packet

## Purpose

Build a **procedurally generated IGVC AutoNav simulation course** in Gazebo/ROS 2.

The simulated course should mimic the real competition setup:

- Fixed overall course shape.
- Fixed oval path.
- Fixed No Man’s Land location.
- Fixed lane/no-lane regions.
- Randomized cones, barricades, painted potholes, ramp position, and lighting.
- Seeded generation so every failed run can be reproduced.

Core concept:

```text
fixed field skeleton + seeded random obstacle placement + validation + Gazebo launch
```

---

# 1. Project Goal

Create a Gazebo world generator that produces a valid IGVC-style AutoNav course every run.

The course should include:

```text
large oval course
painted lane boundaries
traffic cones
traffic barricades
painted pothole discs
one ramp
fixed No Man’s Land area
randomized lighting conditions
```

The exact obstacle and ramp layout should vary per seed.

Example usage:

```bash
python3 scripts/generate_course.py --seed 42 --scenario normal
```

Expected generated files:

```text
generated/generated_world_42.sdf
generated/generated_course_42.yaml
generated/generated_course_42.png
```

Example ROS launch:

```bash
ros2 launch igvc_sim sim_random.launch.py seed:=42 scenario:=normal
```

---

# 2. Fixed vs Randomized Elements

## Fixed Elements

These should not move between generated worlds:

| Element | Fixed? | Notes |
|---|---:|---|
| Course shape | Yes | Large oval/loop |
| Lane marking geometry | Yes | Same painted lane layout |
| No Man’s Land location | Yes | Fixed region |
| Start zone | Yes | Must stay clear |
| Finish zone | Yes | Must stay clear |
| Allowed placement regions | Yes | Defined in YAML |
| Forbidden zones | Yes | Defined in YAML |

## Randomized Elements

These should vary by seed:

| Element | Randomized properties |
|---|---|
| Cones | position, yaw, count |
| Barricades | position, yaw, count |
| Painted potholes | position, radius/size, count |
| Ramp | position, yaw within allowed region |
| Lighting | sun direction, intensity, ambient brightness, shadows |
| Optional sensor realism | camera noise, exposure, GPS noise, IMU bias |

---

# 3. Recommended Repository Layout

```text
igvc_sim/
  config/
    course_regions.yaml
    scenarios.yaml

  launch/
    sim_random.launch.py

  models/
    cone/
      model.sdf
      model.config
    barricade/
      model.sdf
      model.config
    pothole_disc/
      model.sdf
      model.config
    ramp/
      model.sdf
      model.config

  scripts/
    generate_course.py
    validate_course.py
    batch_generate_test.py

  skills/
    gazebo_ros2_skill.md
    igvc_validation_skill.md

  templates/
    autonav_world.sdf.j2

  worlds/
    base_autonav.world.sdf

  generated/
    .gitkeep

  tests/
    test_generation.py
    test_validation.py
```

Generated worlds should generally be ignored by Git except for maybe a few known-good examples.

Suggested `.gitignore`:

```gitignore
generated/*.sdf
generated/*.yaml
generated/*.png
generated/*.log
__pycache__/
.pytest_cache/
```

---

# 4. Required Deliverables

## 4.1 Base Gazebo World

Create:

```text
worlds/base_autonav.world.sdf
```

It should contain:

```text
ground plane
oval course area
painted lane markings
fixed No Man’s Land visual region
start zone marker
finish zone marker
optional grass/field texture
```

The base world should not directly contain the randomized obstacles.

---

## 4.2 Spawnable Gazebo Models

Create or import simple models for:

```text
cone
barricade
painted_pothole_disc
ramp
```

Required properties:

| Model | Visual | Collision | Notes |
|---|---:|---:|---|
| Cone | Yes | Yes | Should be visible to RGB camera and LiDAR/depth if used |
| Barricade | Yes | Yes | Collision geometry required |
| Pothole disc | Yes | Usually no | Painted visual-only flat obstacle |
| Ramp | Yes | Yes | Must have usable collision mesh/box |

Do not over-model. Correct scale beats pretty.

---

## 4.3 Course Region Config

Create:

```text
config/course_regions.yaml
```

Example schema:

```yaml
robot:
  width_m: 0.75
  safety_margin_m: 0.45

regions:
  lane_course:
    polygon:
      - [0.0, 0.0]
      - [20.0, 0.0]
      - [20.0, 10.0]
      - [0.0, 10.0]

  no_mans_land:
    polygon:
      - [8.0, 3.0]
      - [14.0, 3.0]
      - [14.0, 7.0]
      - [8.0, 7.0]

  ramp_allowed:
    polygon:
      - [3.0, 2.0]
      - [17.0, 2.0]
      - [17.0, 8.0]
      - [3.0, 8.0]

forbidden_zones:
  - name: start_zone
    polygon:
      - [0.0, 4.0]
      - [2.0, 4.0]
      - [2.0, 6.0]
      - [0.0, 6.0]

  - name: finish_zone
    polygon:
      - [18.0, 4.0]
      - [20.0, 4.0]
      - [20.0, 6.0]
      - [18.0, 6.0]

ramp:
  approach_clearance_m: 3.0
  exit_clearance_m: 3.0
  side_clearance_m: 1.0
```

Keep geometry configurable. Do not bury course coordinates inside Python unless absolutely necessary.

---

## 4.4 Scenario Config

Create:

```text
config/scenarios.yaml
```

Example:

```yaml
normal:
  cones: [15, 30]
  barricades: [3, 8]
  potholes: [5, 15]
  ramp: true
  lighting: normal
  obstacle_spacing_scale: 1.0

sparse:
  cones: [5, 12]
  barricades: [1, 4]
  potholes: [2, 6]
  ramp: true
  lighting: normal
  obstacle_spacing_scale: 1.0

dense:
  cones: [30, 50]
  barricades: [8, 14]
  potholes: [10, 25]
  ramp: true
  lighting: normal
  obstacle_spacing_scale: 0.8

bad_lighting:
  cones: [15, 30]
  barricades: [3, 8]
  potholes: [5, 15]
  ramp: true
  lighting: randomized_extreme
  obstacle_spacing_scale: 1.0

no_mans_land_dense:
  cones: [10, 20]
  barricades: [5, 10]
  potholes: [5, 15]
  ramp: true
  lighting: normal
  bias_obstacles_to_no_mans_land: true
  obstacle_spacing_scale: 0.9
```

---

# 5. Generator Requirements

Create:

```text
scripts/generate_course.py
```

Required CLI:

```bash
python3 scripts/generate_course.py --seed 42 --scenario normal
```

Also support random seed:

```bash
python3 scripts/generate_course.py --scenario normal
```

Expected terminal output:

```text
Generated course seed: 42
Scenario: normal
World: generated/generated_world_42.sdf
Metadata: generated/generated_course_42.yaml
Preview: generated/generated_course_42.png
Validation: PASS
```

## Required Python Libraries

Recommended:

```text
PyYAML
Shapely
Jinja2
Matplotlib
```

Use:

| Library | Purpose |
|---|---|
| PyYAML | read configs and write metadata |
| Shapely | polygon containment, spacing, collision checks |
| Jinja2 | generate SDF from templates |
| Matplotlib | generate top-down preview PNG |

---

# 6. Placement Rules

## 6.1 General Rules

The generator must enforce:

```text
No object outside legal placement regions.
No object inside forbidden zones.
No object intersecting another object.
No object intersecting the ramp.
No object blocking start/finish.
No obstacle spacing below configured minimum.
```

Recommended base clearance:

```text
minimum_clearance = robot_width_m + safety_margin_m
```

Default:

```text
robot_width_m = 0.75
safety_margin_m = 0.45
minimum_clearance = 1.20 m
```

Dense scenarios may reduce this through `obstacle_spacing_scale`, but they should still be physically possible.

---

## 6.2 Ramp Rules

Ramp is not a normal obstacle. Treat it specially.

Rules:

```text
Exactly one ramp in normal scenarios.
Ramp must be inside ramp_allowed polygon.
Ramp must not overlap cones, barricades, potholes, or forbidden zones.
Ramp must have clear approach corridor.
Ramp must have clear exit corridor.
Ramp yaw should roughly align with expected course travel direction.
Ramp should not be placed sideways unless testing a deliberate edge-case scenario.
```

Recommended clearance values:

```yaml
ramp:
  approach_clearance_m: 3.0
  exit_clearance_m: 3.0
  side_clearance_m: 1.0
```

---

## 6.3 No Man’s Land Rules

No Man’s Land location is fixed.

Inside No Man’s Land:

```text
lane markings are absent
cones may spawn
barricades may spawn
potholes may spawn
ramp should usually not spawn there during MVP
```

Metadata must identify whether each obstacle belongs to:

```text
lane_course
no_mans_land
```

---

# 7. Lighting Randomization

Lighting should vary per generated world.

Randomize:

```text
sun direction
sun intensity
ambient brightness
shadow strength
```

Suggested lighting modes:

```text
normal
bright_overhead
low_angle_sun
overcast_dim
harsh_shadows
randomized_extreme
```

Do not make lighting so bad the course is impossible to perceive. That is not robustness testing. That is bullying the camera.

---

# 8. Metadata Output

Each generated course must save:

```text
generated/generated_course_<seed>.yaml
```

Example:

```yaml
seed: 42
scenario: normal

world_file: generated_world_42.sdf
preview_file: generated_course_42.png

lighting:
  mode: low_angle_sun
  sun_direction: [-0.6, 0.2, -0.8]
  intensity: 0.72
  ambient: 0.35

objects:
  - name: cone_001
    type: cone
    region: lane_course
    pose:
      x: 4.2
      y: 1.8
      z: 0.0
      yaw: 1.57
    radius_m: 0.25

  - name: barricade_001
    type: barricade
    region: no_mans_land
    pose:
      x: 11.3
      y: 5.6
      z: 0.0
      yaw: -0.4
    footprint:
      length_m: 1.2
      width_m: 0.4

ramp:
  name: ramp_001
  pose:
    x: 8.4
    y: 2.7
    z: 0.0
    yaw: 0.0
  footprint:
    length_m: 2.0
    width_m: 1.0
  approach_clearance_passed: true
  exit_clearance_passed: true

validation:
  passed: true
  min_obstacle_spacing_m: 1.2
  blocked_path_check: passed
  forbidden_zone_check: passed
  sdf_check: passed
```

---

# 9. Preview PNG Output

Each generated course must save:

```text
generated/generated_course_<seed>.png
```

The preview should show:

```text
course outline
lane region
No Man’s Land
start zone
finish zone
cones
barricades
potholes
ramp
```

Preview must be generated directly from the same metadata used to generate the SDF.

No parallel truth sources. That is how lies get serialized.

---

# 10. Launch File Requirement

Create:

```text
launch/sim_random.launch.py
```

Required usage:

```bash
ros2 launch igvc_sim sim_random.launch.py seed:=42 scenario:=normal
```

Expected behavior:

```text
generate course world
print seed
print scenario
print generated world path
launch Gazebo with generated world
```

Also support:

```bash
ros2 launch igvc_sim sim_random.launch.py scenario:=dense
```

In this case, generate a random seed and print it.

---

# 11. Validation Requirements

Validation must happen during generation.

Invalid worlds should be rejected and regenerated until valid or until a max-attempt limit is reached.

If max attempts fail, print a useful error:

```text
FAILED: could not generate valid dense course after 100 attempts
Reason: ramp approach corridor blocked
Last seed: 84291
```

## Must Validate

### Fixed Regions

Confirm these do not change:

```text
course boundary
No Man’s Land polygon
start zone
finish zone
lane markings
```

### Reproducibility

Running the same command twice must produce identical metadata:

```bash
python3 scripts/generate_course.py --seed 42 --scenario normal
python3 scripts/generate_course.py --seed 42 --scenario normal
```

Must produce identical:

```text
object count
object positions
object yaw values
ramp position
lighting parameters
metadata content
```

### Randomness

Different seeds should produce meaningfully different layouts:

```bash
python3 scripts/generate_course.py --seed 42 --scenario normal
python3 scripts/generate_course.py --seed 43 --scenario normal
```

Expected differences:

```text
obstacle positions
ramp position
lighting parameters
```

### Collision-Free Placement

Check:

```text
no obstacle footprints overlap
no obstacle intersects ramp
no obstacle intersects forbidden zones
no obstacle is outside allowed regions
```

### Clearance

Check:

```text
minimum gap between obstacles >= configured minimum clearance
```

Default:

```text
1.20 m
```

### Ramp Approach/Exit

Check:

```text
approach corridor clear
exit corridor clear
side clearance clear
ramp inside ramp_allowed polygon
ramp not touching boundaries
```

### Gazebo/SDF Loadability

Check generated world with:

```bash
gz sdf -k generated/generated_world_42.sdf
```

Then check launch:

```bash
gz sim generated/generated_world_42.sdf
```

or equivalent ROS launch.

Must not have:

```text
SDF parse errors
missing model paths
objects below ground
objects falling through floor
physics explosions
```

### Sensor Visibility

Confirm:

```text
cones visible in camera
barricades visible in camera
potholes visible in camera
ramp visible in camera
cones/barricades visible in LiDAR/depth if used
ramp has collision
potholes are visual-only unless intentionally physical
```

### Batch Stability

Create:

```text
scripts/batch_generate_test.py
```

Required usage:

```bash
python3 scripts/batch_generate_test.py --scenario normal --count 100
```

Required result:

```text
100 valid worlds generated
0 validation failures
0 SDF parse failures
all failed seeds logged
```

---

# 12. Definition of Done

The project is done when this works:

```bash
python3 scripts/generate_course.py --seed 42 --scenario normal
```

and produces:

```text
generated/generated_world_42.sdf
generated/generated_course_42.yaml
generated/generated_course_42.png
```

Then this works:

```bash
ros2 launch igvc_sim sim_random.launch.py seed:=42 scenario:=normal
```

and Gazebo launches with:

```text
fixed oval course
fixed No Man’s Land
random cones
random barricades
random painted potholes
one valid ramp
randomized lighting
no invalid overlaps
clear start/finish
valid ramp approach and exit
```

Batch test must pass:

```bash
python3 scripts/batch_generate_test.py --scenario normal --count 100
```

---

# 13. Useful MCPs / Skills

## Recommended MCPs

Use only what helps.

```text
Filesystem MCP, repo-scoped
Fetch or Context7 MCP for docs
optional GitHub MCP later
```

Avoid overloading the agent with unnecessary tools.

## Recommended Skills

```text
git-safe
igvc-sim-cli
gazebo-ros2-skill
igvc-validation-skill
igvc-course-generate
igvc-course-batch-test
igvc-sdf-review
igvc-geometry-review
igvc-preview-review
igvc-regression-seed
```

Minimum useful stack:

```text
repo-scoped file access
terminal/shell access
Git safety workflow
Gazebo/ROS 2 command skill
IGVC validation skill
```

---

# 14. Skill: Gazebo / ROS 2 Simulation Skill

## Skill Name

```text
gazebo-ros2-skill
```

## Purpose

Help the agent create, launch, inspect, and debug Gazebo/ROS 2 simulation assets for the dynamic IGVC AutoNav course.

This skill should be used whenever the agent needs to:

```text
validate SDF syntax
launch generated worlds
check Gazebo model paths
spawn test models
inspect ROS 2 packages
verify launch files
confirm generated worlds load correctly
debug Gazebo startup failures
```

---

## Assumptions

The project is a ROS 2 package named:

```text
igvc_sim
```

Expected workspace pattern:

```text
~/igvc_ws/src/igvc_sim
```

Expected generated world pattern:

```text
igvc_sim/generated/generated_world_<seed>.sdf
```

Expected launch file:

```text
igvc_sim/launch/sim_random.launch.py
```

Gazebo command may be either:

```bash
gz sim
```

or a distro-specific equivalent.

ROS/Gazebo bridge may use:

```text
ros_gz_sim
```

---

## Safe Command Set

The agent may use:

```bash
pwd
ls
find
grep
tree
python3
pytest
colcon build
source install/setup.bash
ros2 pkg list
ros2 pkg prefix igvc_sim
ros2 launch igvc_sim sim_random.launch.py seed:=42 scenario:=normal
gz sdf -k generated/generated_world_42.sdf
gz sim generated/generated_world_42.sdf
```

The agent should avoid:

```bash
sudo
rm -rf
chmod -R 777
curl | bash
docker run --privileged
editing files outside the repo
```

If removal is needed, remove only known generated files inside:

```text
igvc_sim/generated/
```

---

## Common Commands

### Check ROS 2 package visibility

```bash
ros2 pkg list | grep igvc_sim
```

### Build workspace

From workspace root:

```bash
colcon build --symlink-install
source install/setup.bash
```

### Generate one course

From package root:

```bash
python3 scripts/generate_course.py --seed 42 --scenario normal
```

### Validate SDF syntax

```bash
gz sdf -k generated/generated_world_42.sdf
```

### Launch generated world directly

```bash
gz sim generated/generated_world_42.sdf
```

### Launch through ROS 2

```bash
ros2 launch igvc_sim sim_random.launch.py seed:=42 scenario:=normal
```

### Run batch generation test

```bash
python3 scripts/batch_generate_test.py --scenario normal --count 100
```

### Run unit tests

```bash
pytest -q
```

---

## Gazebo/SDF Review Checklist

When reviewing generated SDF, verify:

```text
SDF file exists.
SDF parses with gz sdf -k.
World name is valid.
All model:// paths resolve.
All included model folders have model.config.
All included model folders have model.sdf.
Every included object has a unique name.
Every pose has numeric x, y, z, roll, pitch, yaw.
Ground plane exists.
Random objects are above ground, not underground.
Cones and barricades have collision.
Ramp has collision.
Potholes are visual-only unless explicitly configured otherwise.
Lighting block exists.
Sun direction is normalized or at least sane.
No generated object has NaN or inf values.
```

---

## ROS 2 Launch Review Checklist

When reviewing `sim_random.launch.py`, verify:

```text
seed launch argument exists.
scenario launch argument exists.
random seed is generated if seed is omitted.
chosen seed is printed.
scenario is printed.
generator script is called before Gazebo starts.
generated world path is printed.
Gazebo launches using generated SDF.
launch file works from installed package path, not only source tree.
```

The launch file should not rely on fragile current-working-directory behavior.

Use package path lookup where possible.

---

## Failure Handling

If `gz sdf -k` fails:

```text
inspect the exact line/column
check template syntax
check unescaped characters
check malformed include blocks
check bad pose formatting
```

If Gazebo launches but models are missing:

```text
check GZ_SIM_RESOURCE_PATH
check model:// URI paths
check model.config names
check installed package share directory
```

If ROS 2 launch cannot find the package:

```text
source install/setup.bash
run colcon build
verify package.xml
verify setup.py or CMakeLists.txt
```

If objects fall through ground:

```text
check collision geometry
check z pose
check inertial tags
check ground plane collision
```

If physics explodes:

```text
simplify collision meshes
use primitive boxes/cylinders
check mass/inertia values
avoid tiny/zero inertia
```

---

# 15. Skill: IGVC Dynamic Course Validation Skill

## Skill Name

```text
igvc-validation-skill
```

## Purpose

Validate that a generated IGVC AutoNav course is physically plausible, reproducible, and useful for autonomy testing.

This skill should be used whenever the agent:

```text
writes generate_course.py
writes validate_course.py
changes course_regions.yaml
changes scenarios.yaml
changes SDF templates
changes object placement logic
adds new obstacles
adds lighting randomization
debugs failed generated worlds
```

---

## Required Inputs

The validation skill expects:

```text
config/course_regions.yaml
config/scenarios.yaml
generated/generated_course_<seed>.yaml
generated/generated_world_<seed>.sdf
generated/generated_course_<seed>.png
```

Optional:

```text
generated logs
Gazebo launch output
batch test summary
```

---

## Validation Categories

## A. Config Validation

Check:

```text
course_regions.yaml exists
scenarios.yaml exists
robot width is defined
safety margin is defined
lane_course polygon exists
no_mans_land polygon exists
ramp_allowed polygon exists
forbidden zones exist
start zone exists
finish zone exists
all polygons have at least 3 points
all polygon points are numeric
all polygons are valid Shapely polygons
```

Failure examples:

```text
polygon self-intersects
missing no_mans_land region
robot width not configured
ramp_allowed region missing
```

---

## B. Seed Reproducibility

Run:

```bash
python3 scripts/generate_course.py --seed 42 --scenario normal
cp generated/generated_course_42.yaml /tmp/course_42_a.yaml

python3 scripts/generate_course.py --seed 42 --scenario normal
cp generated/generated_course_42.yaml /tmp/course_42_b.yaml

diff /tmp/course_42_a.yaml /tmp/course_42_b.yaml
```

Pass condition:

```text
No diff.
```

If the diff contains timestamps, random UUIDs, unordered dictionaries, or nondeterministic file paths, fix the generator.

Metadata should be deterministic for a fixed seed.

---

## C. Seed Diversity

Run:

```bash
python3 scripts/generate_course.py --seed 42 --scenario normal
python3 scripts/generate_course.py --seed 43 --scenario normal
```

Pass condition:

```text
At least obstacle positions, ramp position, or lighting differ.
```

Fail condition:

```text
Different seeds generate identical layouts.
```

---

## D. Object Count Validation

For each scenario:

```text
cone count within configured range
barricade count within configured range
pothole count within configured range
ramp count matches scenario
```

Example:

```yaml
normal:
  cones: [15, 30]
```

Pass condition:

```text
15 <= cone_count <= 30
```

---

## E. Region Containment

For each object:

```text
object center inside allowed region
object footprint inside allowed region where practical
object not inside forbidden zone
object not outside course boundary
```

For circular objects:

```text
Point(x, y).buffer(radius)
```

For rectangular objects:

```text
rotated rectangle footprint
```

Use Shapely for both.

---

## F. Collision / Overlap Validation

Check every object pair:

```text
footprint_i.intersects(footprint_j) == false
```

Or, better:

```text
footprint_i.distance(footprint_j) >= required_clearance
```

Use the configured clearance:

```text
minimum_clearance = robot_width_m + safety_margin_m
```

Dense scenarios may scale the value:

```text
effective_clearance = minimum_clearance * obstacle_spacing_scale
```

---

## G. Ramp Validation

Check:

```text
exactly one ramp in normal scenario
ramp footprint inside ramp_allowed polygon
ramp footprint outside forbidden zones
ramp does not intersect obstacles
ramp approach corridor is clear
ramp exit corridor is clear
ramp yaw is sane
```

Suggested approach/exit corridor model:

```text
rectangular region extending from ramp front/back
length = approach_clearance_m or exit_clearance_m
width = ramp_width_m + 2 * side_clearance_m
```

Pass condition:

```text
No obstacles intersect approach corridor.
No obstacles intersect exit corridor.
```

---

## H. Start/Finish Validation

Check:

```text
start zone clear
finish zone clear
no objects inside start zone
no objects inside finish zone
ramp not inside start or finish
```

These zones should stay boring. Boring start zones save debugging hours.

---

## I. No Man’s Land Validation

Check:

```text
No Man’s Land polygon is fixed.
No Man’s Land is visible in preview.
Objects inside No Man’s Land are tagged region: no_mans_land.
Objects outside No Man’s Land are not mislabeled.
Lane markings do not appear inside No Man’s Land unless intentionally modeled.
```

---

## J. Lighting Validation

Check:

```text
lighting metadata exists
sun direction exists
sun intensity exists
ambient value exists
values are numeric
intensity is within configured range
ambient is within configured range
lighting changes between different seeds
```

Avoid:

```text
zero light
negative intensity
NaN
fully black world
fully blown-out world
```

---

## K. Preview PNG Validation

Check:

```text
preview PNG exists
preview PNG is non-empty
preview shows course outline
preview shows No Man’s Land
preview shows start/finish zones
preview shows ramp
preview object count matches metadata
```

Optional automated check:

```text
file exists and size > 10 KB
image can be opened by PIL
metadata object count equals plotted object count recorded by generator
```

---

## L. SDF Validation

Run:

```bash
gz sdf -k generated/generated_world_42.sdf
```

Pass condition:

```text
No SDF parse errors.
```

Also inspect:

```text
all model includes use valid model:// names
all names are unique
poses are valid
lighting block exists
ground plane exists
```

---

## M. Gazebo Launch Validation

Run:

```bash
gz sim generated/generated_world_42.sdf
```

or:

```bash
ros2 launch igvc_sim sim_random.launch.py seed:=42 scenario:=normal
```

Pass condition:

```text
Gazebo opens.
World loads.
No missing model errors.
Objects are visible.
Objects are not underground.
Physics is stable.
```

---

## N. Batch Validation

Run:

```bash
python3 scripts/batch_generate_test.py --scenario normal --count 100
python3 scripts/batch_generate_test.py --scenario dense --count 50
python3 scripts/batch_generate_test.py --scenario bad_lighting --count 50
```

Pass condition:

```text
0 validation failures
0 SDF parse failures
all failed seeds logged if any fail
```

If failures occur, output should include:

```text
seed
scenario
failure reason
generated metadata path
preview image path
world path
```

---

# 16. Suggested Validation Script Behavior

Create:

```text
scripts/validate_course.py
```

Usage:

```bash
python3 scripts/validate_course.py generated/generated_course_42.yaml
```

Expected output:

```text
Validation report for seed 42
Scenario: normal

[PASS] Config loaded
[PASS] Fixed regions valid
[PASS] Object counts in range
[PASS] Region containment
[PASS] Forbidden zones clear
[PASS] Object spacing
[PASS] Ramp placement
[PASS] Ramp approach/exit
[PASS] Start/finish clear
[PASS] Preview exists
[PASS] SDF exists

Validation: PASS
```

Failure output example:

```text
Validation report for seed 57
Scenario: dense

[PASS] Config loaded
[PASS] Fixed regions valid
[PASS] Object counts in range
[FAIL] Object spacing
       cone_014 too close to barricade_002
       distance: 0.62 m
       required: 0.96 m

Validation: FAIL
```

---

# 17. Suggested Unit Tests

Create:

```text
tests/test_generation.py
tests/test_validation.py
```

Recommended tests:

```text
test_same_seed_same_metadata
test_different_seed_different_metadata
test_object_counts_within_scenario_ranges
test_no_objects_in_forbidden_zones
test_no_object_overlaps
test_ramp_inside_allowed_region
test_ramp_approach_exit_clear
test_preview_file_created
test_sdf_file_created
test_batch_generation_10_worlds
```

Example pytest command:

```bash
pytest -q
```

---

# 18. Implementation Priorities

## Phase 1 — MVP

Build:

```text
base world
simple models
region YAML
scenario YAML
seeded generator
metadata output
preview PNG
basic validation
ROS launch
```

## Phase 2 — Robustness

Add:

```text
ramp approach/exit validation
batch generation testing
unit tests
better SDF checks
lighting scenarios
```

## Phase 3 — Realism

Add:

```text
camera noise profiles
GPS drift
IMU bias
wheel slip zones
ground texture variation
fog/haze
wet/dry grass variants
```

Do not start with Phase 3. That is how projects become haunted Blender files.

---

# 19. Agent Work Rules

The agent should:

```text
make small commits
run tests after each meaningful change
record failing seeds
prefer deterministic scripts
keep generated files out of Git
avoid editing outside the repo
avoid sudo
avoid broad filesystem access
```

Before large changes:

```bash
git status
git diff
git checkout -b dynamic-autonav-generator
```

After meaningful working change:

```bash
pytest -q
git status
git diff
```

Commit only source/config/template/test files unless explicitly told otherwise.

---

# 20. Final Acceptance Checklist

The agent should not call the task done until:

```text
generate_course.py works with explicit seed
generate_course.py works with random seed
same seed produces same metadata
different seed produces different layout
generated SDF passes gz sdf -k
Gazebo loads generated world
ROS launch works
preview PNG is created
metadata YAML is created
validate_course.py passes
batch_generate_test.py passes 100 normal worlds
start and finish zones remain clear
No Man’s Land stays fixed
ramp has clear approach and exit
objects do not overlap
object counts respect scenario config
lighting changes between seeds
```

Final demo commands:

```bash
python3 scripts/generate_course.py --seed 42 --scenario normal
python3 scripts/validate_course.py generated/generated_course_42.yaml
gz sdf -k generated/generated_world_42.sdf
ros2 launch igvc_sim sim_random.launch.py seed:=42 scenario:=normal
python3 scripts/batch_generate_test.py --scenario normal --count 100
```

If all pass, the dynamic course generator is functional.
