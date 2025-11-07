from ftplib import parse229
from pydantic import BaseModel, Field, field_validator
import numpy as np
from scipy.optimize import root_scalar
from control_agent.sys import FOPDT, ControllerPI

ZN_PROCEDURE = """
## Ziegler-Nichols Closed-Loop (Ultimate Gain) Method
The Ziegler-Nichols closed loop method is based on experiments executed on an
established control loop (a real system or a simulated system).

The tuning procedure is as follows:

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
"""

class UltimatePoint(BaseModel):
    """Ultimate point for P-only control."""
    K_u: float = Field(..., description="Ultimate gain")
    P_u: float = Field(..., description="Ultimate period [s]")
    omega_u: float = Field(..., description="Ultimate rad/s (for reference)")

class ZieglerNicholsMethod:
    def __init__(self, sys_pars: FOPDT):
        self.sys_pars = sys_pars
        self.ultimate_point = self.get_ultimate_point()
        self.pi_controller = self.zn_tuning()

    def _phase_balance(self, w: float) -> float:
        """phase condition f(ω) = ωL + atan(ωT) - π = 0"""
        T, L = self.sys_pars.T, self.sys_pars.L
        return w * L + np.arctan(w * T) - np.pi

    def _find_phase_root(self, bracket: tuple[float, float], **kwargs) -> float:
        """
        Find ω such that phase_condition(ω)=0.
        Uses SciPy's default method (Brent's algorithm) with a bracketed interval.
        """
        sol = root_scalar(self._phase_balance, bracket=bracket, **kwargs)
        if not sol.converged:
            raise RuntimeError("Root finding did not converge.")
        return float(sol.root)
    
    def _build_bracket(self, L: float) -> tuple[float, float]:
        """
        Build a robust bracket [a, b] for the root of phase_balance(w) = 0.
        f(0) = −π < 0, f(ω→∞) → +∞, so we expand b until f(b) > 0.
        """
        a = 1e-12
        b = max(np.pi / L, (np.pi / (2.0 * L)) * 2.5)
        fb = self._phase_balance(b)
        tries = 0
        while fb <= 0.0 and tries < 50:
            b *= 2.0
            fb = self._phase_balance(b)
            tries += 1
        if fb <= 0.0:
            raise RuntimeError("Failed to bracket ultimate frequency; check K,T,L.")
        return a, b

    def get_ultimate_point(self, xtol: float = 1e-10, maxiter: int = 200) -> UltimatePoint:
        """
        Compute (K_u, P_u) for P-only feedback via the FOPTD parameters.
        Uses a robust bisection on f(w)=w*L + atan(w*T) - pi.
        Raises ValueError if no ultimate point exists (e.g. L = 0).
        """
        K, T, L = self.sys_pars.K, self.sys_pars.T, self.sys_pars.L
        if L == 0.0:
            raise ValueError("No ultimate point for L=0 (phase never reaches -π).")

        # find robusrt bounds for bracket
        bracket = self._build_bracket(L)

        # find ultimate frequency throug scalar root finding 
        omega_u = self._find_phase_root(bracket, xtol=xtol, maxiter=maxiter)

        # Magnitude condition: |K G(jωu)| = 1  ⇒  Ku = √(1+(ωu T)^2)/|K|
        K_u = float(np.sqrt(1.0 + (omega_u * T) ** 2) / abs(K))
        P_u = float(2.0 * np.pi / omega_u)

        return UltimatePoint(K_u=K_u, P_u=P_u, omega_u=omega_u)

    def zn_tuning(self):
        """Get the Ziegler-Nichols PI controller parameters"""
        K_u = self.ultimate_point.K_u
        P_u = self.ultimate_point.P_u

        return ControllerPI(K_p=0.45 * K_u, T_i=P_u / 1.2)

zn = ZieglerNicholsMethod(sys_pars=FOPDT(K=2.0, T=1.0, L=0.5))



        
