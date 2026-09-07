import time

def run(conn, manifest):
    vessel = conn.space_center.active_vessel
    control = vessel.control
    flight = vessel.flight()
    targets = manifest.get("nominal_targets", {})

    print("[GNC] Ignition command sent.")
    control.throttle = 1.0
    control.activate_next_stage()

    time.sleep(3.0)
    control.activate_next_stage() # Liftoff clamps release
    print("[GNC] Liftoff confirmed.")

    # 1. Graphite Vane Pitch Steering
    vane_engaged = False
    while flight.mean_altitude < 35000:
        met = vessel.met
        if 12.0 <= met <= 18.0 and not vane_engaged:
            print("[GNC] Applying analog pitch vane deflection...")
            control.pitch = 0.02
            vane_engaged = True
        elif met > 18.0 and vane_engaged:
            print("[GNC] Neutralizing vanes.")
            control.pitch = 0.0
            vane_engaged = False
        time.sleep(0.05)

    # 2. Monitor Burnout (MECO)
    print("[GNC] Monitoring powered ascent...")
    while vessel.thrust > 1000.0:
        time.sleep(0.05)

    print(f"[GNC] MECO at MET: {vessel.met:.2f} s. Entering suborbital coast.")
    control.throttle = 0.0

    # 3. Track Suborbital Arc through Peak Apogee
    print("[GNC] Coasting toward apogee...")
    while flight.vertical_speed > 0:
        time.sleep(0.5)

    print(f"[GNC] APOGEE PASS CONFIRMED: {flight.mean_altitude / 1000.0:.2f} km.")
    
    # 4. Allow continuous recording during descent
    while flight.mean_altitude > 1000:
        time.sleep(1.0)
