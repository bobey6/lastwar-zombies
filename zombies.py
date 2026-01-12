#!/usr/bin/env python3
"""
zombies.py

Flow:
1) Wait until events.png is visible (confidence=0.85), then click it
2) Look for search.png:
   - If found within 5 seconds: click it
   - If NOT found within 5 seconds: start over (go back to events.png)
3) Wait until attack.png is visible, then click it
4) Look for march.png for up to 5 seconds:
   - If found: click it, then start over
   - If NOT found within 5 seconds:
       a) look for return_attack.png within 5 seconds
          - if not found, wait 10 seconds and try again (repeat)
       b) once return_attack.png IS found, click it
       c) then wait for march.png, click it, then start over

Global safety:
- If ANY step cannot be completed in 5 minutes, perform recovery:
    base.png (click) -> world.png (click) -> start over
"""

import time
from datetime import datetime
import pyautogui

# --- Settings ---
CONFIDENCE = 0.85  # all images

POLL_INTERVAL = 0.25

SEARCH_TIMEOUT_SECONDS = 5
MARCH_TIMEOUT_SECONDS = 5

RETURN_ATTACK_TIMEOUT_SECONDS = 5
RETURN_ATTACK_RETRY_SLEEP_SECONDS = 10

STEP_MAX_SECONDS = 5 * 60  # 5 minutes global per-step cap

# Images
EVENTS_IMG = "events.png"
SEARCH_IMG = "search.png"
ATTACK_IMG = "attack.png"
MARCH_IMG = "march.png"
RETURN_ATTACK_IMG = "return_attack.png"
BASE_IMG = "base.png"
WORLD_IMG = "world.png"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Some PyAutoGUI/PyScreeze versions raise an exception when image isn't found.
try:
    from pyscreeze import ImageNotFoundException as PyscreezeImageNotFound  # type: ignore
except Exception:
    PyscreezeImageNotFound = Exception


def find_image_center(image_path: str, confidence: float):
    """Return (x,y) if found else None. Never raises on 'not found'."""
    try:
        box = pyautogui.locateOnScreen(image_path, confidence=confidence)
    except (pyautogui.ImageNotFoundException, PyscreezeImageNotFound):
        return None

    if box is None:
        return None

    pt = pyautogui.center(box)
    return (int(pt.x), int(pt.y))


def wait_up_to(image_path: str, confidence: float, timeout_seconds: float, poll_interval: float):
    """Wait up to timeout_seconds; return (x,y) if found else None."""
    end = time.time() + timeout_seconds
    while time.time() < end:
        pt = find_image_center(image_path, confidence)
        if pt is not None:
            return pt
        time.sleep(poll_interval)
    return None


def wait_until_found_with_deadline(image_path: str, confidence: float, max_seconds: float, poll_interval: float):
    """Wait up to max_seconds; return (x,y) if found else None."""
    return wait_up_to(image_path, confidence, max_seconds, poll_interval)


def click_at(pt, image_name: str):
    pyautogui.moveTo(pt[0], pt[1], duration=0.05)
    pyautogui.click(pt[0], pt[1])
    print(f"[{ts()}] Clicked {image_name} at {pt}")


def recovery():
    """
    Recovery sequence:
      base.png (click) -> world.png (click) -> return to caller (caller restarts loop)
    Each recovery step is also capped at STEP_MAX_SECONDS to avoid hanging forever.
    """
    print(f"[{ts()}] Recovery triggered: attempting {BASE_IMG} -> {WORLD_IMG} then restart.")

    pt_base = wait_until_found_with_deadline(BASE_IMG, CONFIDENCE, STEP_MAX_SECONDS, POLL_INTERVAL)
    if pt_base is None:
        print(f"[{ts()}] Recovery: {BASE_IMG} not found within 5 minutes; restarting anyway.")
        return
    click_at(pt_base, BASE_IMG)

    pt_world = wait_until_found_with_deadline(WORLD_IMG, CONFIDENCE, STEP_MAX_SECONDS, POLL_INTERVAL)
    if pt_world is None:
        print(f"[{ts()}] Recovery: {WORLD_IMG} not found within 5 minutes; restarting anyway.")
        return
    click_at(pt_world, WORLD_IMG)

    print(f"[{ts()}] Recovery complete; restarting.")


def main():
    print(f"[{ts()}] Starting loop. FAILSAFE is ON (move mouse to top-left to stop).")

    while True:
        # STEP 1: events.png (must complete within 5 minutes)
        pt_events = wait_until_found_with_deadline(EVENTS_IMG, CONFIDENCE, STEP_MAX_SECONDS, POLL_INTERVAL)
        if pt_events is None:
            print(f"[{ts()}] Step timeout: {EVENTS_IMG} not found within 5 minutes.")
            recovery()
            continue
        print(f"[{ts()}] Found {EVENTS_IMG} at {pt_events} (confidence={CONFIDENCE})")
        click_at(pt_events, EVENTS_IMG)

        # STEP 2: search.png within 5 seconds; if not, restart to events
        pt_search = wait_up_to(SEARCH_IMG, CONFIDENCE, SEARCH_TIMEOUT_SECONDS, POLL_INTERVAL)
        if pt_search is None:
            print(f"[{ts()}] {SEARCH_IMG} not found within {SEARCH_TIMEOUT_SECONDS}s; restarting at {EVENTS_IMG}.")
            continue
        click_at(pt_search, SEARCH_IMG)

        # STEP 3: attack.png (must complete within 5 minutes)
        pt_attack = wait_until_found_with_deadline(ATTACK_IMG, CONFIDENCE, STEP_MAX_SECONDS, POLL_INTERVAL)
        if pt_attack is None:
            print(f"[{ts()}] Step timeout: {ATTACK_IMG} not found within 5 minutes.")
            recovery()
            continue
        click_at(pt_attack, ATTACK_IMG)

        # STEP 4A: march.png quick check (5 seconds)
        pt_march = wait_up_to(MARCH_IMG, CONFIDENCE, MARCH_TIMEOUT_SECONDS, POLL_INTERVAL)
        if pt_march is not None:
            click_at(pt_march, MARCH_IMG)
            print(f"[{ts()}] March clicked; restarting at {EVENTS_IMG}.")
            continue

        # STEP 4B: march not found quickly -> return_attack loop, but capped to 5 minutes total
        print(f"[{ts()}] {MARCH_IMG} not found within {MARCH_TIMEOUT_SECONDS}s; looking for {RETURN_ATTACK_IMG}.")

        return_attack_deadline = time.time() + STEP_MAX_SECONDS
        while True:
            remaining = return_attack_deadline - time.time()
            if remaining <= 0:
                print(f"[{ts()}] Step timeout: {RETURN_ATTACK_IMG} not found within 5 minutes.")
                recovery()
                break  # restart outer cycle

            pt_return = wait_up_to(
                RETURN_ATTACK_IMG,
                CONFIDENCE,
                min(RETURN_ATTACK_TIMEOUT_SECONDS, remaining),
                POLL_INTERVAL,
            )
            if pt_return is not None:
                click_at(pt_return, RETURN_ATTACK_IMG)

                # After finding return_attack, wait for march.png, but also capped to 5 minutes
                pt_march2 = wait_until_found_with_deadline(MARCH_IMG, CONFIDENCE, STEP_MAX_SECONDS, POLL_INTERVAL)
                if pt_march2 is None:
                    print(f"[{ts()}] Step timeout: {MARCH_IMG} not found within 5 minutes after {RETURN_ATTACK_IMG}.")
                    recovery()
                    break

                click_at(pt_march2, MARCH_IMG)
                print(f"[{ts()}] March clicked after return_attack; restarting at {EVENTS_IMG}.")
                break

            print(
                f"[{ts()}] {RETURN_ATTACK_IMG} not found within {RETURN_ATTACK_TIMEOUT_SECONDS}s; "
                f"waiting {RETURN_ATTACK_RETRY_SLEEP_SECONDS}s then retrying..."
            )
            time.sleep(min(RETURN_ATTACK_RETRY_SLEEP_SECONDS, max(0, return_attack_deadline - time.time())))


if __name__ == "__main__":
    main()
