from pydantic import BaseModel, Field, field_validator

class ControllerPI(BaseModel):
    """PI-controller parameters"""
    K_p: float = Field(..., description="Proportional gain")
    T_i: float = Field(..., description="Integral time")

class FOPDT(BaseModel):
    """
    First-Order Plus Dead Time (FOPDT) system model.

    This model represents the parameters of a first-order continuous-time open-loop stable dynamic system with time delay by:
        G(s) = (K * exp(-L * s)) / (T * s + 1)

    Parameters
    ----------
    K : float
        Static process gain. Represents the steady-state change in the output
        per unit change in input. The sign indicates the control direction
        (positive for direct-acting, negative for reverse-acting processes).

    T : float
        Process time constant [s]. Defines the characteristic time for the
        output to reach approximately 63.2% of its total steady-state change
        after the delay has elapsed. Must be strictly positive.

    L : float
        Effective time delay or dead time [s]. Models transport lag, signal
        transmission delay, or actuator/sensor latency. Must be non-negative.
    """

    K: float = Field(..., description="Static process gain (output/input ratio). May be positive or negative.")
    T: float = Field(..., description="Process time constant in seconds. Must be strictly positive.")
    L: float = Field(..., description="Effective time delay (dead time) in seconds. Must be non-negative.")

    # --- Validators ---
    @field_validator("K")
    @classmethod
    def validate_gain(cls, v: float) -> float:
        if v == 0:
            raise ValueError("Process gain K must be non-zero.")
        return v

    @field_validator("T")
    @classmethod
    def validate_time_constant(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Time constant T must be strictly positive.")
        return v

    @field_validator("L")
    @classmethod
    def validate_time_delay(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Time delay L must be non-negative.")
        return v

