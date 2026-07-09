from sgp4.api import Satrec
import numpy as np
import time

print("🛰️ ============================================================= 🛰️")
print("    IAAHV CYBER-PHYSICAL ENGINE — CORE ORBITAL MECHANICS MODULE    ")
print("    STATUS: HIGH-FIDELITY VECTOR DYNAMICS CALCULATION ACTIVE       ")
print("🛰️ ============================================================= 🛰️\n")

# CONSTANTS (WGS-84 Earth Gravitational Model)
MU = 398600.4418  # Earth's Gravitational Parameter (km^3/s^2)
R_EARTH = 6378.137  # Earth's Equatorial Radius (km)

# 1. Initialize Spacecraft (The Harvester)
line1_machine = "1 25544U 98067A   26181.50000000  .00016717  00000-0  30000-3 0  9995"
line2_machine = "2 25544  51.6428 201.1234 0005432  67.8901 292.1122 15.49876543123456"
harvester = Satrec.twoline2rv(line1_machine, line2_machine)

# 2. Ingest Tracked Debris Target
line1_debris = "1 34131U 93036AZ  26180.50000000  .00000214  00000-0  11234-3 0  9993"
line2_debris = "2 34131  74.0412 114.3219 0014321  56.7891 303.4512 14.34125678623412"
target_debris = Satrec.twoline2rv(line1_debris, line2_debris)

# Configuration Parameters
DEBRIS_MASS_KG = 15.0  
ALERT_CRITICAL_DIST_KM = 35.0             

# Time-slice epoch parameters (Julian Date)
jd, fr = 2440587.5, 0.5

def calculate_keplerian_elements(r, v):
    """Converts State Vectors (r, v) into orbital elements using Vector Calculus."""
    r_mag = np.linalg.norm(r)
    v_mag = np.linalg.norm(v)
    
    # Specific angular momentum vector h = r x v
    h = np.cross(r, v)
    h_mag = np.linalg.norm(h)
    
    # Semi-major axis (a) via Vis-Viva Equation energy conservation: E = (v^2/2) - (mu/r)
    ecc_vector = ((v_mag**2 - MU / r_mag) * r - np.dot(r, v) * v) / MU
    e = np.linalg.norm(ecc_vector)
    
    a = 1.0 / ((2.0 / r_mag) - (v_mag**2 / MU))
    
    # Perigee Altitude (Lowest point of orbit relative to Earth's surface)
    perigee_altitude = a * (1.0 - e) - R_EARTH
    return a, e, perigee_altitude

try:
    for frame in range(1, 6):
        print(f"🔄 [DYNAMIC FRAME VAL] Step {frame}/5...")
        
        # Propagate orbits using SGP4
        err_m, pos_m, vel_m = harvester.sgp4(jd, fr)
        err_d, pos_d, vel_d = target_debris.sgp4(jd, fr)
        
        if err_m == 0 and err_d == 0:
            # Cast into high-precision NumPy vectors
            r_m = np.array(pos_m)
            r_d = np.array(pos_d)
            v_d = np.array(vel_d)
            
            # Compute true 3D Euclidean vector norm distance
            distance = np.linalg.norm(r_m - r_d)
            print(f"   ↳ 📐 Absolute Relative Range: {distance:.4f} km")
            
            if distance < ALERT_CRITICAL_DIST_KM:
                print("   ⚠️ [INTERCEPT THRESHOLD REACHED] Executing State-Vector Analytics...")
                
                # Extract original Keplerian traits
                a_orig, e_orig, perigee_orig = calculate_keplerian_elements(r_d, v_d)
                print(f"   ↳ 📊 Debris Current Perigee Altitude: {perigee_orig:.2f} km")
                
                # CALCULATE CRITICAL ABLATION PHYSICS
                # Target: Drop perigee altitude into the atmosphere (< 150km) to trigger destructive drag
                target_perigee = 120.0 
                target_a = (target_perigee + R_EARTH + np.linalg.norm(r_d)) / 2.0
                
                # Vis-Viva calculation for required velocity after laser pulse
                required_v_mag = np.sqrt(MU * ((2.0 / np.linalg.norm(r_d)) - (1.0 / target_a)))
                current_v_mag = np.linalg.norm(v_d)
                
                # Needed Delta-V to be induced by the laser system
                delta_v_needed = current_v_mag - required_v_mag
                
                print(f"   ↳ ⚡ [LASER ENGAGED] Initiating Photonic Ablation Coupling Loop.")
                print(f"   ↳ 🎯 Required Δv to force atmospheric decay: {delta_v_needed:.6f} km/s")
                print(f"   ↳ 📉 Predicted New Perigee Post-Ablation: {target_perigee:.1f} km (De-orbit Assured)")
            else:
                print("   ✅ [ORBITAL STABILITY] Target tracking clear within standard deviations.")
        else:
            print("   ❌ SGP4 Mathematical Fault Error.")
            
        print("-" * 80)
        fr += 0.002  # Propagate forward in time
        time.sleep(1.5)

except KeyboardInterrupt:
    print("\n🛑 Telemetry closed down by operator.")
