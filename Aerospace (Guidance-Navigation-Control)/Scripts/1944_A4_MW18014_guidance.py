import time

class SoundingGravityTurn:
    def __init__(self, conn, params):
        self.conn = conn
        self.params = params
        self.vessel = conn.space_center.active_vessel
        self.control = self.vessel.control

    def execute(self):
        print(f"[GUIDANCE] Proportional Analog Guidance Initialized for {self.vessel.name}...")
        
        # Kill all stock PID / Autopilot interference
        try:
            self.vessel.auto_pilot.disengage()
        except Exception:
            pass
        self.control.sas = False
        self.control.pitch = 0.0
        self.control.yaw = 0.0
        self.control.roll = 0.0
        self.control.throttle = 1.0

        flight = self.vessel.flight()

        # STAGING
        print("[GUIDANCE] Stage 1: Igniting Engine...")
        self.control.activate_next_stage()
        time.sleep(2.0)
        print("[GUIDANCE] Stage 2: Releasing Clamps...")
        self.control.activate_next_stage()

        start_time = self.vessel.met
        kicked = False

        # ASCENT LOOP (Using tiny analog vane deflections, NOT PID)
        while True:
            met = self.vessel.met
            alt = flight.mean_altitude
            thrust = self.vessel.thrust

            # Engine Brennschluss / Flameout
            if alt > 5000 and thrust < 100.0:
                print(f"[GUIDANCE] MECO / Brennschluss detected at: {alt/1000.0:.1f} km (MET: {met:.1f}s)")
                break

            # Gentle aerodynamic pitch kick: only 2% surface deflection
            if met >= self.params["pitch_kick_time"] and met < (self.params["pitch_kick_time"] + self.params["pitch_kick_duration"]):
                if not kicked:
                    print("[GUIDANCE] Applying gentle 2% pitch kick eastward...")
                    kicked = True
                self.control.pitch = -0.02  # Tiny deflection down
                self.control.yaw = 0.02    # Heading northeast
            else:
                # Return vanes to neutral and let aerodynamic fins naturally hold prograde
                self.control.pitch = 0.0
                self.control.yaw = 0.0

            time.sleep(0.05)

        # ENGINE CUT: Reset controls completely
        self.control.pitch = 0.0
        self.control.yaw = 0.0
        self.control.roll = 0.0
        
        orbit = self.vessel.orbit
        print(f"[GUIDANCE] Coast to space. Target Apogee: {orbit.apoapsis_altitude / 1000.0:.2f} km")

        # COAST TO APOGEE
        while flight.vertical_speed > -5.0:
            time.sleep(1.0)

        print("[GUIDANCE] Apogee crossed! Spacecraft falling back to Earth...")

        # DESCENT
        # Keep controls 100% neutral so when air hits, fins naturally weather-cock the craft
        while flight.mean_altitude > 3000:
            time.sleep(2.0)

        print("[GUIDANCE] Terminal descent complete.")
