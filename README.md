# zombies-pyautogui

Automates a repeating in-game click sequence using **Python + PyAutoGUI** image matching.

## What it does

The script continuously performs this loop:

1. **Find and click `events.png`** (confidence **0.85**)
2. **Find `search.png` within 5 seconds**
   - If found: click it
   - If not found: restart from `events.png`
3. **Find and click `attack.png`**
4. **Try to find `march.png` within 5 seconds**
   - If found: click it, then restart from `events.png`
   - If not found:
     - Look for `return_attack.png` (retry: search up to 5s, then wait 10s, repeat)
     - When `return_attack.png` is found: click it
     - Then wait for `march.png` (up to 5 minutes) and click it
     - Restart from `events.png`

### Global recovery (failsafe navigation)

If **any step cannot be completed within 5 minutes**, the script attempts to recover by:

1. Find and click `base.png`
2. Find and click `world.png`
3. Restart the main loop

## Requirements

- Python 3.9+ recommended (works on newer versions as well)
- `pyautogui`
- `opencv-python` (required for `confidence=` image matching)

Install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install pyautogui opencv-python
