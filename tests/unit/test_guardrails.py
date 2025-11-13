"""Unit tests for guardrail system."""

import os
import pytest
from unittest.mock import Mock, MagicMock
from pydantic import BaseModel

from control_agent.agent.guardrails import (
    GuardrailViolation,
    GuardrailValidator,
    SimulationGuardrails,
    apply_guardrails
)
from control_agent.agent.ctx import ToolExecutionError
from control_agent.agent.common import (
    SimulationStepResponseProps,
    StepProps,
    IdentificationProps,
    FOPDTModel,
    LambdaTuningProps,
    StateSnapshotEvent,
    RunContext,
    StateDeps,
    SimContext,
    FmuContext,
    SimulationRun,
    FOPDTCheck,
    LambdaTuningCheck,
    ZNPIDTuningCheck,
    PIDParameters,
    EventType,
)


class TestGuardrailViolation:
    """Test GuardrailViolation model"""
    
    def test_guardrail_violation_creation(self):
        violation = GuardrailViolation(
            field="test_field",
            value=100,
            constraint="max=50",
            message="Test violation"
        )
        assert violation.field == "test_field"
        assert violation.value == 100
        assert violation.constraint == "max=50"
        assert violation.message == "Test violation"


class TestSimulationGuardrails:
    """Test SimulationGuardrails validator"""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance"""
        return SimulationGuardrails()
    
    @pytest.fixture
    def mock_ctx(self):
        """Create a mock context"""
        ctx = Mock(spec=RunContext)
        ctx.deps.state.fmu_names = ["PI_FOPDT_2", "PI_FOPDT_3"]
        ctx.deps.state.fmu = Mock()
        ctx.deps.state.fmu.model_description = None
        ctx.deps.state.fmu.simulations = []
        return ctx
    
    def test_validate_input_simulate_step_response_time_exceeds_max(self, validator):
        """Test that simulation time exceeding max is caught"""
        sim_props = Mock()
        sim_props.start_time = 0
        sim_props.stop_time = 2000.0  # Exceeds default max of 1000
        sim_props.step_size = 1.0
        sim_props.output_interval = 0.1
        
        violations = validator.validate_input(
            "simulate_step_response",
            sim_props=sim_props,
            step_props=None
        )
        
        assert len(violations) > 0
        assert any(v.field == "simulation_time" for v in violations)
    
    def test_validate_input_simulate_step_response_valid(self, validator):
        """Test that valid simulation inputs pass"""
        sim_props = Mock()
        sim_props.start_time = 0
        sim_props.stop_time = 10.0
        sim_props.step_size = 1.0
        sim_props.output_interval = 0.1
        
        step_props = Mock()
        step_props.time_range = Mock()
        step_props.time_range.sampling_time = 0.1
        step_props.initial_value = 0
        step_props.final_value = 1
        
        violations = validator.validate_input(
            "simulate_step_response",
            sim_props=sim_props,
            step_props=step_props
        )
        
        assert len(violations) == 0
    
    def test_validate_input_simulate_step_response_step_size_exceeds_max(self, validator):
        """Test that step size exceeding max is caught"""
        sim_props = Mock()
        sim_props.start_time = 0
        sim_props.stop_time = 10.0
        sim_props.step_size = 20.0  # Exceeds default max of 10
        sim_props.output_interval = 0.1
        
        violations = validator.validate_input(
            "simulate_step_response",
            sim_props=sim_props,
            step_props=None
        )
        
        assert len(violations) > 0
        assert any(v.field == "step_size" for v in violations)
    
    def test_validate_input_simulate_step_response_sampling_time_too_small(self, validator):
        """Test that sampling time below minimum is caught"""
        sim_props = Mock()
        sim_props.start_time = 0
        sim_props.stop_time = 10.0
        sim_props.step_size = 1.0
        sim_props.output_interval = 0.1
        
        step_props = Mock()
        step_props.time_range = Mock()
        step_props.time_range.sampling_time = 0.0001  # Below minimum
        step_props.initial_value = 0
        step_props.final_value = 1
        
        violations = validator.validate_input(
            "simulate_step_response",
            sim_props=sim_props,
            step_props=step_props
        )
        
        assert len(violations) > 0
        assert any(v.field == "sampling_time" for v in violations)
    
    def test_validate_input_choose_fmu_path_traversal(self, validator):
        """Test that path traversal in FMU name is caught"""
        violations = validator.validate_input(
            "choose_fmu",
            fmu_name="../malicious.fmu"
        )
        
        assert len(violations) > 0
        assert any(v.field == "fmu_name" and "path traversal" in v.message.lower() for v in violations)
    
    def test_validate_input_choose_fmu_not_in_list(self, validator, mock_ctx):
        """Test that FMU not in available list is caught"""
        violations = validator.validate_input(
            "choose_fmu",
            fmu_name="NONEXISTENT",
            ctx=mock_ctx
        )
        
        assert len(violations) > 0
        assert any(v.field == "fmu_name" for v in violations)
    
    def test_validate_input_choose_fmu_valid(self, validator, mock_ctx):
        """Test that valid FMU name passes"""
        violations = validator.validate_input(
            "choose_fmu",
            fmu_name="PI_FOPDT_2",
            ctx=mock_ctx
        )
        
        assert len(violations) == 0
    
    def test_validate_input_identify_fopdt_no_simulations(self, validator, mock_ctx):
        """Test that identify_fopdt requires simulations"""
        mock_ctx.deps.state.fmu.simulations = []
        
        violations = validator.validate_input(
            "identify_fopdt_from_step",
            props=Mock(),
            ctx=mock_ctx
        )
        
        assert len(violations) > 0
        assert any(v.field == "simulations" for v in violations)
    
    def test_validate_input_lambda_tuning_no_fopdt(self, validator, mock_ctx):
        """Test that lambda_tuning requires FOPDT checks"""
        mock_ctx.deps.state.fmu.simulations = [Mock()]
        mock_ctx.deps.state.fmu.simulations[0].fopdt_checks = []
        
        violations = validator.validate_input(
            "lambda_tuning",
            props=Mock(),
            ctx=mock_ctx
        )
        
        assert len(violations) > 0
        assert any(v.field == "fopdt_checks" for v in violations)
    
    def test_validate_output_fopdt_invalid_k(self, validator):
        """Test that invalid FOPDT K parameter is caught"""
        # Create a mock result with invalid K
        fopdt_model = Mock()
        fopdt_model.K = -1.0  # Invalid: must be > 0
        fopdt_model.T = 1.0
        fopdt_model.L = 0.5
        
        fopdt_check = Mock()
        fopdt_check.data = fopdt_model
        
        simulation = Mock()
        simulation.fopdt_checks = [fopdt_check]
        
        fmu = Mock()
        fmu.simulations = [simulation]
        
        snapshot = Mock()
        snapshot.fmu = fmu
        
        result = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=snapshot
        )
        
        violations = validator.validate_output("identify_fopdt_from_step", result)
        
        assert len(violations) > 0
        assert any(v.field == "K" for v in violations)
    
    def test_validate_output_fopdt_invalid_t(self, validator):
        """Test that invalid FOPDT T parameter is caught"""
        fopdt_model = Mock()
        fopdt_model.K = 1.0
        fopdt_model.T = -1.0  # Invalid: must be > 0
        fopdt_model.L = 0.5
        
        fopdt_check = Mock()
        fopdt_check.data = fopdt_model
        
        simulation = Mock()
        simulation.fopdt_checks = [fopdt_check]
        
        fmu = Mock()
        fmu.simulations = [simulation]
        
        snapshot = Mock()
        snapshot.fmu = fmu
        
        result = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=snapshot
        )
        
        violations = validator.validate_output("identify_fopdt_from_step", result)
        
        assert len(violations) > 0
        assert any(v.field == "T" for v in violations)
    
    def test_validate_output_fopdt_invalid_l(self, validator):
        """Test that invalid FOPDT L parameter is caught"""
        fopdt_model = Mock()
        fopdt_model.K = 1.0
        fopdt_model.T = 1.0
        fopdt_model.L = -0.1  # Invalid: must be >= 0
        
        fopdt_check = Mock()
        fopdt_check.data = fopdt_model
        
        simulation = Mock()
        simulation.fopdt_checks = [fopdt_check]
        
        fmu = Mock()
        fmu.simulations = [simulation]
        
        snapshot = Mock()
        snapshot.fmu = fmu
        
        result = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=snapshot
        )
        
        violations = validator.validate_output("identify_fopdt_from_step", result)
        
        assert len(violations) > 0
        assert any(v.field == "L" for v in violations)
    
    def test_validate_output_tool_execution_error_skipped(self, validator):
        """Test that ToolExecutionError results skip validation"""
        error = ToolExecutionError(message="Test error")
        violations = validator.validate_output("simulate_step_response", error)
        assert len(violations) == 0


class TestApplyGuardrails:
    """Test apply_guardrails wrapper function"""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance"""
        return SimulationGuardrails()
    
    def test_apply_guardrails_disabled(self, validator):
        """Test that guardrails can be disabled"""
        def test_tool(x: int) -> int:
            return x * 2
        
        wrapped = apply_guardrails(test_tool, validator, "test_tool", enabled=False)
        assert wrapped(5) == 10
    
    def test_apply_guardrails_input_violation(self, validator):
        """Test that input violations are caught"""
        def test_tool(sim_props) -> str:
            return "success"
        
        # Create invalid sim_props
        sim_props = Mock()
        sim_props.start_time = 0
        sim_props.stop_time = 2000.0  # Exceeds max
        sim_props.step_size = 1.0
        
        wrapped = apply_guardrails(test_tool, validator, "simulate_step_response", enabled=True)
        result = wrapped(sim_props=sim_props)
        
        assert isinstance(result, ToolExecutionError)
        assert "Guardrail violation" in result.message
    
    def test_apply_guardrails_valid_input(self, validator):
        """Test that valid inputs pass through"""
        def test_tool(x: int) -> int:
            return x * 2
        
        wrapped = apply_guardrails(test_tool, validator, "test_tool", enabled=True)
        result = wrapped(x=5)
        assert result == 10
    
    def test_apply_guardrails_exception_handling(self, validator):
        """Test that exceptions are caught and converted to ToolExecutionError"""
        def test_tool(x: int) -> int:
            raise ValueError("Test error")
        
        wrapped = apply_guardrails(test_tool, validator, "test_tool", enabled=True)
        result = wrapped(x=5)
        
        assert isinstance(result, ToolExecutionError)
        assert "Test error" in result.message
    
    def test_apply_guardrails_positional_args(self, validator):
        """Test that positional arguments are handled correctly"""
        def test_tool(ctx, value: int) -> int:
            return value * 2
        
        mock_ctx = Mock()
        wrapped = apply_guardrails(test_tool, validator, "test_tool", enabled=True)
        result = wrapped(mock_ctx, 5)
        assert result == 10


class TestGuardrailConfiguration:
    """Test guardrail configuration from environment"""
    
    def test_guardrail_config_from_env(self, monkeypatch):
        """Test that guardrails read configuration from environment"""
        monkeypatch.setenv("MAX_SIMULATION_TIME", "500.0")
        monkeypatch.setenv("MAX_STEP_SIZE", "5.0")
        
        validator = SimulationGuardrails()
        assert validator.MAX_SIMULATION_TIME == 500.0
        assert validator.MAX_STEP_SIZE == 5.0
    
    def test_guardrail_config_defaults(self):
        """Test that guardrails use defaults when env vars not set"""
        validator = SimulationGuardrails()
        assert validator.MAX_SIMULATION_TIME == 1000.0
        assert validator.MAX_STEP_SIZE == 10.0

