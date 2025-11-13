# Ziegler Nichols (Closed-Loop) Tuning Method
The Ziegler-Nichols closed loop method is based on experiments executed on an
established control loop (a real system or a simulated system).

## Step-by-Step Procedure
1. Bring the process to (or as close to as possible) the specified operating
   point of the control system to ensure that the controller during the tuning
   is "feeling" representative process dynamics and to minimize the chance that
   variables during the tuning reach limits.

   You can bring the process to the operating point by manually adjusting the
   control variable, with the controller in manual mode, until the process
   variable is approximately equal to the setpoint.

2. Turn the PID controller into a P controller by setting set Ti = ∞.
   Initially set gain Kp = 0.

3. Increase Kp until there are sustained oscillations in the signals in the
   control system, e.g. in the process measurement, after an excitation of the
   system. (The sustained oscillations corresponds to the system being on the
   stability limit.) This Kp value is denoted the ultimate (or critical) gain,
   K_u.
   
   **How to Identify Sustained Oscillations:**
- Use `find_peaks` tool after each simulation to analyze the output signal
- **Sustained oscillations** (what you need for Ku):
  * At least 3-4 peaks detected
  * Peak amplitudes remain approximately constant (within 10-20% variation)
  * Peak periods are consistent (low variance in `average_peak_period`)
  * This indicates the system is at the stability limit
- **Growing oscillations**: Peak amplitudes increase over time → Kp is too high, reduce it
- **Decaying oscillations**: Peak amplitudes decrease over time → Kp is too low, increase it
- **No oscillations**: Fewer than 3 peaks → Kp is too low, increase it

4. Measure the ultimate (or critical) period Pu of the sustained oscillations.

5. Calculate the controller parameter values according to Table 1, and use
   these parameter values in the controller.

**Table 1:** Ziegler-Nichols closed-loop tuning rules for P, PI, and PID
controllers.

| Controller Type | Kp expression | Ti expression | Td expression |
|-----------------|----------------|----------------|----------------|
| P controller    | 0.5 Ku         | ∞              | 0              |
| PI controller   | 0.45 Ku        | Pu / 1.2       | 0              |
| PID controller  | 0.6 Ku         | Pu / 2         | Pu / 8 = Ti / 4|
