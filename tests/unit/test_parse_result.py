import pytest
from control_agent.evals.utils import parse_result


@pytest.fixture
def sample_system_params():
    """Sample system parameters used across multiple tests"""
    return {'K': 1.0, 'T': 1.0, 'L': 0.5}


def test_parse_dict_returns_dict(sample_system_params):
    """Test that dict input returns dict"""
    parsed = parse_result(sample_system_params)
    assert parsed == sample_system_params
    assert isinstance(parsed, dict)


def test_parse_object_with_dict(sample_system_params):
    """Test that object with __dict__ returns dict"""
    class TestObject:
        def __init__(self, data):
            self.K = data['K']
            self.T = data['T']
            self.L = data['L']
    
    obj = TestObject(sample_system_params)
    parsed = parse_result(obj)
    assert parsed == sample_system_params


def test_parse_object_with_data_attribute(sample_system_params):
    """Test that object with data attribute recursively parses"""
    class TestObject:
        def __init__(self, data):
            self.data = data
    
    obj = TestObject(sample_system_params)
    parsed = parse_result(obj)
    assert parsed == sample_system_params


def test_parse_pydantic_model_with_model_dump(sample_system_params):
    """Test that Pydantic model with model_dump() returns dict"""
    class TestModel:
        def model_dump(self):
            return sample_system_params
    
    model = TestModel()
    parsed = parse_result(model)
    assert parsed == sample_system_params


def test_parse_pydantic_model_with_dict(sample_system_params):
    """Test that Pydantic model with dict() returns dict"""
    class TestModel:
        def dict(self):
            return sample_system_params
    
    model = TestModel()
    parsed = parse_result(model)
    assert parsed == sample_system_params


def test_parse_nested_data_attribute(sample_system_params):
    """Test that nested data attributes are parsed recursively"""
    class InnerObject:
        def __init__(self, data):
            self.data = data
    
    class OuterObject:
        def __init__(self, data):
            self.data = InnerObject(data)
    
    obj = OuterObject(sample_system_params)
    parsed = parse_result(obj)
    assert parsed == sample_system_params


def test_parse_unsupported_type_returns_none():
    """Test that unsupported types return None"""
    assert parse_result("string") is None
    assert parse_result(123) is None
    assert parse_result([1, 2, 3]) is None


def test_parse_none_returns_none():
    """Test that None input returns None"""
    assert parse_result(None) is None


def test_parse_empty_dict():
    """Test that empty dict returns empty dict"""
    assert parse_result({}) == {}


def test_parse_object_with_empty_dict():
    """Test that object with empty __dict__ returns empty dict"""
    class EmptyObject:
        pass
    
    obj = EmptyObject()
    parsed = parse_result(obj)
    assert parsed == {}


def test_parse_complex_nested_structure():
    """Test parsing complex nested structure"""
    class ControllerParams:
        def __init__(self):
            self.Kp = 0.5
            self.Ti = 1.0
    
    class SystemParams:
        def __init__(self):
            self.K = 1.0
            self.T = 1.0
            self.L = 0.5
            self.controller = ControllerParams()
    
    obj = SystemParams()
    parsed = parse_result(obj)
    assert 'K' in parsed
    assert 'T' in parsed
    assert 'L' in parsed
    assert 'controller' in parsed
    assert parsed['K'] == 1.0
    assert parsed['T'] == 1.0
    assert parsed['L'] == 0.5
