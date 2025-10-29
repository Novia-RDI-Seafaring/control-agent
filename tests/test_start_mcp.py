import pytest

@pytest.fixture
def server():
    return "foo"


@pytest.mark.asyncio
async def test_server(server):
    assert server == "foo"