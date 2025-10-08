# Lambda (λ) Tuning Method — Experimental Procedure

The **Lambda tuning method** is a model-based approach used to determine PI or PID controller parameters that achieve a desired closed-loop time constant, λ. This experiment outlines the practical steps to perform Lambda tuning on a real or simulated process approximated by a **First-Order Plus Dead-Time (FOPDT)** model.

---

## Step-by-Step Procedure

1. **Perform a Step Test**

   - Keep the controller in **manual mode**.  
   - Apply a **small step change** in the control signal (e.g., 5–10% of its range).  
   - Record the system response until it settles.

2. **Identify FOPDT Parameters**

   Identify the system parameters $K$, $T$, and $L$ of a FOPDT model fitted to the step response.  
   The parameters can be identified using this simple procedure:

   - Perform a step change of size $u_\mathrm{step}$ at time $t = t_\mathrm{step}$ and record:
       - $t_0$: the time when the output first starts to change.  
       - $y_\infty$: the final steady-state value of the output.  
       - $t_{63}$: The time it takes for the response to reach **63% of its total change** (excluding dead time), i.e., $y(t_0~+~t_{63})~=~0.63\,y_\mathrm{step}$.

   - Compute:

     **Dead time:** $L = t_0 - t_\mathrm{step}$
     

     **Static gain:** $K = \frac{y_\infty}{u_\mathrm{step}}$

     **Time constant:** $T = t_{63}$
     
     *(Note that $t_{63}$ is measured from the start of the response, excluding the dead time.)*

3. **Select Desired λ (Lambda)**

   Choose λ based on the desired balance between performance and robustness:

   - $\lambda = L \quad \text{(fast/aggressive response)}$
   - $\lambda = 2L \quad \text{(balanced response)}$
   - $\lambda = 3L \quad \text{(conservative/stable response)}$

   If $L \approx 0$, use: $\lambda = kT, \quad k \in [0.2, 1]$

4. **Compute Controller Parameters**

   Once $K$, $T$, $L$, and $λ$ are known, compute the **PI controller** gains:

   - Controller gain: $K_p = \frac{T}{K(\lambda + L)}$
   - Controller integral time constant: $T_i = T$

   For large dead-time systems, use the modified form:
   $$
   K_p = \frac{T + 0.5L}{K(\lambda + 0.5L)}, \quad T_i = T + 0.5L
   $$
