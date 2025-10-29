import os
from dotenv import load_dotenv
load_dotenv(override=True)

from pydantic_ai.ag_ui import AGUIApp
from agent.core import create_agent

print(os.getenv("OPENAI_API_KEY"))

# Create your agent
agent = create_agent()

# Create AG-UI app (this is a Starlette app, not FastAPI)
app = AGUIApp(agent)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)