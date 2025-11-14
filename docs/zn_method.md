# Ziegler–Nichols Closed-Loop Tuning Procedure (AI-Ready Version)

## Goal
Determine PID tuning parameters using the Ziegler–Nichols closed-loop (ultimate gain) method.

---

## Procedure

### 1. Initial configuration
- Set the controller to **manual** mode.  
- Set **Ti = ∞** (disable integral action).  
- Set **Td = 0** (disable derivative action).

---

### 2. Perform repeated simulation runs to find sustained oscillations

**Pseudocode (concise):**  
- Start with a small gain: `Kp = 0.1`.  
- Run a step-response simulation.  
- Analyze the oscillation behavior:  
  - If oscillations **decay**, increase `Kp` and run again.  
  - If oscillations **grow**, decrease `Kp` and retry.  
  - If oscillations are **sustained (constant amplitude)** → stop.  
- The `Kp`, when sustained oscillation are obtained, is called the **ultimate gain Ku**.

---

### 3. Measure the ultimate period (Pu)
- Measure the **average period time between peaks** of the sustained oscillations to get the **ultimate period Pu**.  

---

### 4. Compute controller parameters using Ziegler–Nichols rules.