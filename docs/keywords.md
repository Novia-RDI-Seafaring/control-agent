# Keywords and Descriptions Used in Process Control

| **Term** | **Description** |
|-----------|-----------------|
| **FOPDT (First-Order Plus Dead Time)** | A simple model representing many real processes:  $G(s) = \dfrac{K e^{-Ls}}{Ts + 1}$. Characterized by **process gain (K)**, **time constant (T)**, and **dead time (L)**. |
| **Process Gain (K)** | The steady-state change in output divided by the change in input (Δy/Δu). Indicates how sensitive the process is. |
| **Time Constant (T)** | The time it takes the output to reach about 63% of its total change after a step input. Reflects the speed of the process. |
| **Dead Time (L)** | The pure delay before the process output begins to respond after an input change. Often caused by transport delay or sensor lag. |
| **Static Gain** | Same as process gain; ratio between steady-state output and input change. |
| **Process Reaction Curve** | The open-loop step response curve used to estimate FOPDT parameters (K, T, L). |
| **Step Test** | A test where the input is suddenly changed (step), and the resulting output response is recorded to identify system dynamics. |
| **Open-Loop Test** | A test performed without feedback control; used to determine process parameters from the reaction curve. |
| **Closed-Loop Test** | A test done while the PID controller is active; used in tuning methods such as the Ziegler–Nichols closed-loop test. |
| **Ultimate Gain (Ku)** | The proportional gain at which the system just starts to oscillate continuously in closed loop (sustained oscillations). |
| **Ultimate Period (Pu)** | The oscillation period corresponding to the ultimate gain. Used in Ziegler–Nichols tuning formulas. |
| **Critical Gain** | Another term for **ultimate gain (Ku)**. |
| **Critical Period** | Another term for **ultimate period (Pu)**. |
| **Ziegler–Nichols Method** | A classical PID tuning approach based on Ku and Pu. Provides formulas for P, PI, and PID parameters to achieve quarter-amplitude damping. |
| **Cohen–Coon Method** | A tuning method based on open-loop step response and FOPDT model parameters. Useful for processes with significant dead time. |
| **Lambda Tuning (IMC Tuning)** | A method based on desired closed-loop time constant (λ). Balances speed and robustness by selecting λ relative to T. |
| **IMC (Internal Model Control)** | A control design framework where the controller is derived from the inverse of the process model, filtered for robustness. |
| **Closed-Loop Time Constant (λ)** | Desired speed of the closed-loop response in Lambda/IMC tuning. Typically between 0.5T and 2T depending on aggressiveness. |
| **Aggressiveness (of Tuning)** | Describes how fast the controller responds; smaller λ → more aggressive control. |
| **Model Fit Error** | The difference between the real process response and the model (FOPDT) response; used to validate identification accuracy. |
| **Dead-Time Ratio (L/T)** | The ratio of dead time to time constant; indicates how challenging the process is to control. |
| **Self-Regulating Process** | A process that naturally reaches a new steady-state after a step input (e.g., temperature control). |

---

## PID Controller Parameters and Related Terms

| **Term** | **Description** |
|-----------|-----------------|
| **PID Controller** | A controller that combines **Proportional (P)**, **Integral (I)**, and **Derivative (D)** actions to reduce error and improve response. Its general form is:  $G_c(s) = K_p \left(1 + \dfrac{1}{T_i s} + T_d s \right)$. |
| **Kp (Proportional Gain)** | Determines the controller output proportional to the current error. Higher Kp increases responsiveness but can cause oscillations or instability. |
| **Ti (Integral Time)** | The time over which the integral term sums the error. Shorter Ti increases the integral effect, reducing steady-state error but potentially causing overshoot. |
| **Td (Derivative Time)** | The time constant for the derivative term. It anticipates future error based on the rate of change, improving stability and reducing overshoot. |
| **Proportional Term (P)** | Reacts to the present error: $P = K_p \cdot e(t)$. Provides immediate correction but leaves steady-state error. |
| **Integral Term (I)** | Reacts to accumulated error: $I = K_p \dfrac{1}{T_i} \int e(t)\,dt$. Eliminates steady-state error but may cause slow or oscillatory behavior. |
| **Derivative Term (D)** | Reacts to the rate of change of error: $D = K_p T_d \dfrac{de(t)}{dt}$. Adds damping and helps prevent overshoot. |
| **Controller Output (u)** | The control signal sent to the process:  $u(t) = K_p \left[e(t) + \dfrac{1}{T_i}\int e(t)dt + T_d\dfrac{de(t)}{dt}\right]$. |
| **PI Controller** | Combines P and I terms to remove steady-state error while avoiding noise sensitivity from the derivative term. |
| **PD Controller** | Combines P and D terms for faster response and less overshoot, often used in motion or position control. |
| **Integral Windup** | Condition where the integral term accumulates excessive error during saturation, leading to large overshoot or slow recovery. |
| **Anti-Windup** | A strategy that limits or resets the integral term when the controller output saturates. |
| **Controller Gain (Gc)** | The transfer function of the controller in the Laplace domain, representing its frequency response and behavior. |
| **Tuning Parameters** | The set of PID coefficients (Kp, Ti, Td) adjusted to achieve desired performance—speed, stability, and minimal overshoot. |
| **Tuning Robustness** | The ability of the tuned controller to maintain performance despite modeling errors or disturbances. |
| **Derivative Filter (N)** | A low-pass filter added to the derivative term to reduce amplification of measurement noise:  $G_d(s) = \dfrac{T_d s}{(T_d / N) s + 1}$. |
| **Overshoot** | The amount by which the process output exceeds the desired setpoint during transient response, usually expressed as a percentage of the final value. High overshoot indicates an overly aggressive tuning. |
| **Undershoot** | The amount by which the process output initially falls below the setpoint (or desired value) before stabilizing. Often seen after a load disturbance or in oscillatory responses. |
| **Tuning Rules** | Empirical or analytical methods (e.g., Ziegler–Nichols, Cohen–Coon, Lambda) that relate process model parameters to optimal PID settings. |
