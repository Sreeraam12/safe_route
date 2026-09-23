# SafeRoute Personal Digital Twin Dataset (Chennai City)

> **IMPORTANT NOTICE: SYNTHETIC DEVELOPMENT DATA**  
> All files in this directory are synthetic development datasets generated specifically for testing, architecture validation, and research ablation studies within the Chennai metropolitan area. They do NOT contain real personal identifiers, Aadhaar numbers, private messages, or uncurated private trip tracking data.

## Archetypes Included
1. **Safety First** (`usr_arch_safety_01`): Prioritizes well-lit, low-isolation, highly populated corridors; high detour tolerance.
2. **Time Sensitive** (`usr_arch_time_02`): Prioritizes directness and minimal travel time with lower detour tolerance.
3. **Balanced** (`usr_arch_balanced_03`): Equitable trade-off between detour penalty and safety factors.
4. **Night Sensitive** (`usr_arch_night_04`): Stringent nighttime avoidance penalties on dark or isolated roads.
5. **Weather Sensitive** (`usr_arch_weather_05`): High aversion to poorly drained, low-visibility, or flood-prone corridors.

## File Manifest
- `01_personal_users.csv`: Coarse profile archetypes.
- `02_personal_preferences.csv`: Initial baseline preferences (normalized 0.0 - 1.0).
- `03_personal_trips.csv`: Historical trip records between major Chennai zones.
- `04_route_interactions.csv`: Candidate route impressions, choices, and rejection rationales.
- `05_personal_feedback.csv`: Post-trip subjective ratings and feedback signals.
- `06_personal_segment_memory.csv`: Road-segment-level familiarity and trust memory.
- `07_personal_twin_state.csv`: Calibrated dynamic twin weights and model confidence values.
