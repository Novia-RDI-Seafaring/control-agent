\begin{table*}[t!]
\centering
\caption{Experiment queries and expected tool calls and outcomes.}
\label{tab:experiment_queries}
\renewcommand{\arraystretch}{1.2}
\begin{tabularx}{\linewidth}{@{}p{0.10\linewidth} p{0.30\linewidth} p{0.30\linewidth} X@{}}
\toprule
\textbf{Experiment} & \textbf{Query} & \textbf{Expected Tool Calls} & \textbf{Expected Output} \\
\midrule
1 &
Simulate an open-loop step response with input change from 0 to 1. Return the output as a \texttt{DataModel} with timesteps 1 seconds. &
Generate a step input, set the controller to mode ``manual'', and simulate using the \texttt{simulate\_fmu} tool. &
Return open-loop step response as \texttt{DataModel}. \\

2 &
Simulate a closed-loop step response with input change from 0 to 1 &
Generate a step input, set the controller to mode ``automatic'', and simulate using the \texttt{simulate\_fmu} tool. &
Return closed-loop step response. \\

3 &
Make a step response and identify the static gain $K$, time constant $T$, and dead time $L$ of a FOPDT model &

Repeat Experiment 1 and extract parameters $K$, $T$, and $L$ from the step response. & Return $K$, $T$, and $L$. \\

4 &
Tune the PI controller with Lambda tuning with $\lambda = 1.0$ &
Repeat Experiment 1 and compute controller parameters as $K_c = \dfrac{T}{K(\lambda + L)}$, $T_i = T$.
& Return $K_c$ and $T_i$. \\

5 &
Tune the PI controller with Lambda tuning for fast response &
Repeat Experiment 1 and compute controller parameters as $K_c = \dfrac{T}{K(\lambda + L)}$, $T_i = T$ for $\lambda \approx L$.
& Return $K_c$ and $T_i$. \\

6 &
Tune the PI controller with Lambda tuning for a balanced response &
Repeat Experiment 1 and compute controller parameters as $K_c = \dfrac{T}{K(\lambda + L)}$, $T_i = T$ for $\lambda \approx T$.
& Return $K_c$ and $T_i$. \\

7 &
Tune the PI controller with Lambda tuning for a robust response &
Repeat Experiment 1 and compute controller parameters as $K_c = \dfrac{T}{K(\lambda + L)}$, $T_i = T$ for $\lambda \ge 2T$.
& Return $K_c$ and $T_i$. \\

8 &
Tune the PI controller using Ziegler--Nichols closed-loop method &
Initially, set $T_i >> 0$ and a small value of $K_p$ and simulate with \texttt{simulate\_fmu} tool. Repeatedly increase $K_p$ and simulate until sustained oscillations are obtained. Record the critical gain $K_u$ and period time $T_u$. Compute $K_p = 0.45K_u$, $T_i = \dfrac{T_u}{1.2}$.
& Return $K_c$ and $T_i$. \\
\bottomrule
\end{tabularx}
\end{table*}