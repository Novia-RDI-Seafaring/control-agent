from ftplib import parse229
from pydantic import BaseModel, Field, field_validator
import numpy as np
from scipy.optimize import root_scalar
from mcp_fmi_ecc26.sys import FOPDT, ControllerPI

LAMBDA_TUNING_PROCEDURE = """
"""


class LambdaTuningMethod:
    def __init__(
        self,
        sys_pars: FOPDT,
        lam: float = 1.0,
    ):
        """
        Lambda (λ) is the desired closed-loop time constant, typically set to about
        1-3 times the process dead time L: smaller for faster response, and larger
        for greater robustness. For systems with negligible dead time, lambda is
        typically set i nthe range 0.2 - 1 times the process time constant T.
        """
        self.lam = lam
        self.sys_pars = sys_pars
        self.pi_controller = self.lambda_tuning(self.lam)

    def lambda_tuning(self, lam: float):
        """
        Get the lambda-tuning PI controller parameters.
        """
        K, T, L = self.sys_pars.K, self.sys_pars.T, self.sys_pars.L
        Kp = T / (K * (lam + L))
        Ti = T
        return ControllerPI(K_p=Kp, T_i=Ti)


sys = FOPDT(K=1.0, T=1.0, L=1.0)
lam = LambdaTuningMethod(sys_pars=sys, lam=2.0)
