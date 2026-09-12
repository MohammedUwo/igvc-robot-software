# Simulation

## `dynamic-autonav-course/`

Generates seeded, IGVC-style AutoNav courses as Gazebo worlds — asphalt platform, white lane
markings, obstacles, and ramps — from a grid of prevalidated lane tiles. Same seed, same course,
so a run is reproducible.

```bash
python3 scripts/generate_course.py --seed 42 --scenario normal --template oval_with_chicane
```

Each run writes an `.sdf` world, a `.yaml` describing the lane polylines and obstacle positions, a
preview `.png`, and debug output under `generated/`.

The `generated/` directory is not committed — it was 34 MB of output worlds. Regenerate what you
need; the seed is all you have to keep.

Load one into the sim with:

```bash
ros2 launch diff_drive_robot robot.launch.py world:=<path>/generated/generated_world_42.sdf
```

This is the closest thing the team has to a practice course that doesn't need a parking lot and a
roll of tape, and it's the right place to shake out lane detection before going outside.
