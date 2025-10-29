
from pydantic_ai import Agent, ModelMessage
from mcp_fmi_ecc26.agent import ask, get_history
import datetime
import uuid
from pydantic import BaseModel

from fasthtml.common import *
import sys
sys.path.insert(0, '..')
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, Resource
from opentelemetry.instrumentation.fmpy import FmpyInstrumentor
from mcp_fmi_ecc26.utils.fmu import list_fmus
import fasthtml_otel as ft_otel
# Create FastHTML app

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
resource = Resource.create({"service.name": "MCP-FMI ECC26 Demo"})
provider = TracerProvider(resource=resource)

app = FastHTML(exts="ws")
streamer = ft_otel.configure(
    app,
    provider,
    auto_expand_patterns=[],
    endpoint=f"/telemetry-{uuid.uuid4()}"
)
# Instrument Pydantic AI (renderer-agnostic)
logger.debug("Instrumenting Pydantic AI")
ft_otel.instrument_pydantic_ai(provider)

logger.debug("Instrumenting FMPy")
FmpyInstrumentor().instrument()

logger.debug("Getting tracer")
tracer = provider.get_tracer("Ft Otel Streamer Demo")



# Chat messages storage
messages = []

class ChatMessage(BaseModel):
    role: str
    content: str
    idx: int

    def __ft__(self):
        bubble = "chat-bubble-primary" if self.role == "user" else "chat-bubble-secondary"
        align = "chat-end" if self.role == "user" else "chat-start"
        return Div(
            Div(self.role, cls="chat-header text-xs opacity-70"),
            Div(self.content, id=f"chat-content-{self.idx}", cls=f"chat-bubble {bubble}"),
            id=f"chat-message-{self.idx}",
            cls=f"chat {align}"
        )
        return self.model_dump_json()


def ChatInput():
    """Render chat input field."""
    return Input(
        type="text",
        name="msg",
        id="msg-input",
        placeholder="Ask me to roll a die...",
        cls="input input-bordered w-full",
        hx_swap_oob="true",
    )


@app.ws("/ws")
async def chat_socket(session_id: str, msg: str, fmu_id: str, send):
    global history
    """Handle chat WebSocket messages."""
    print(f"Chat message: {msg}")
    print(f"FMU ID: {fmu_id}")
    print(f"Session ID: {session_id}")
    tracer = provider.get_tracer("Ft Otel Streamer Demo")
    with tracer.start_as_current_span(f"User message", attributes={"user_message": msg.strip()}) as span:
        # Add user message
        span.set_attribute("fmu_id", fmu_id.strip())
        span.set_attribute("message", msg.strip())
        messages = get_history(session_id)
        msgc = ChatMessage(role="user", content=msg.strip(), idx=len(messages))
        await send(Div(msgc, hx_swap_oob="beforeend", id="chatlist"))
        await send(ChatInput())

        # Process with AI agent
        try:
            with tracer.start_as_current_span("ai_processing") as ai_span:
                reply = await ask(msg + f" (fmu file: {fmu_id})", session_id)
                span.set_attribute("reply", reply)


        except Exception as e:
            reply = f"Error: {e} (Check OPENAI_API_KEY environment variable)"
            span.set_attribute("error", True)
            span.set_attribute("error_message", str(e))

        await send(Div(ChatMessage(role="assistant", content=reply, idx=len(messages)-1), hx_swap_oob="beforeend", id="chatlist"))


@app.get("/")
def index(session):
    
    session_id = session.get("session_id", str(uuid.uuid4()))
    
    """Main page with telemetry demo."""
    with tracer.start_as_current_span("page_render") as span:
        span.set_attribute("page", "index")
        span.set_attribute("user_agent", "demo")

        return Title("FastHTML Opentelemetry Streamer"), Body(
            Div(
                H1("FastHTML Opentelemetry Streamer", cls="text-3xl font-bold text-center mb-8"),


                # Main content area
                Div(
                    # Left: Telemetry streaming
                    Div(
                        ft_otel.telemetry_container(),
                        cls="w-2/3 pr-4"
                    ),

                    # Right: Chat interface
                    Div(
                        H2("Agent Chat", cls="text-xl font-bold mb-4"),

                        Div(
                            *[ChatMessage(i) for i in range(len(messages))],
                            id="chatlist",
                            cls="h-[50vh] overflow-y-auto bg-base-200 p-4 rounded-lg mb-4"
                        ),

                        Form(
                            Input(type="hidden", name="session_id", value=session_id),
                            Group(Select(
                                *[Option(f, value=f) for f in list_fmus()],
                                name="fmu_id",
                                id="fmu-select",
                                cls="select select-bordered w-full"
                            )),
                            Group(ChatInput(), Button("Send", cls="btn btn-primary")),
                            hx_ext="ws",
                            ws_send=True,
                            ws_connect="/ws",
                            onsubmit="return false;",
                            cls="flex gap-2 mt-2"
                        ),

                        cls="w-1/3 pl-4"
                    ),

                    cls="flex gap-4"
                ),

                # Footer
                Div(
                    P(
                        "This demo shows real-time ",
                        A("OpenTelemetry", href="https://opentelemetry.io/", target="_blank", cls="underline"),
                        " streaming with ",
                        A("FastHTML", href="https://www.fastht.ml/", target="_blank", cls="underline"),
                        cls="text-center text-sm opacity-70 mt-8"
                    ),
                    P(
                        "It is built as part of the ",
                        A("Virtual Sea Trial Project (VST)", href="https://virtualseatrial.fi/", target="_blank", cls="underline"),
                        ", Funded by Business Finland",
                        cls="text-center text-sm opacity-70"
                    ),
                    P(
                        "Source code: ",
                        A("github.com/Novia-RDI-Seafaring/ft-otel", href="https://github.com/Novia-RDI-Seafaring/ft-otel", target="_blank", cls="underline"),
                        cls="text-center text-sm opacity-70"
                    ),
                    P(
                        "Source code: ",
                        A("github.com/Novia-RDI-Seafaring/ft-otel", href="https://github.com/Novia-RDI-Seafaring/mcp-fmi-ecc26", target="_blank", cls="underline"),
                        cls="text-center text-sm opacity-70"
                    ),
                    Details(
                        Summary("Citation", cls="text-center text-sm opacity-70 cursor-pointer mt-4"),
                        Pre(
                            """@software{fasthtml_otel,
  title={MCP-FMI ECC26 Demo},
  author={Christoffer Björkskog, Mikael Manngårt, Lamin Jatta},
  year={2025},
  url={https://github.com/Novia-RDI-Seafaring/mcp-fmi-ecc26}
}""",
                            cls="text-xs bg-base-200 p-2 rounded mt-2 overflow-x-auto"
                        ),
                        cls="mt-4"
                    ),
                    cls="mt-8"
                ),

                cls="container mx-auto px-4 py-8"
            )
        )

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=os.getenv("SIMULATION_UI_PORT", 8002))
    parser.add_argument('--host', type=str, default=os.getenv("SIMULATION_UI_HOST", "localhost"))
    parser.add_argument('--folder', type=str, default=os.getenv("SIMULATION_FMU_FOLDER", "models/fmus/"))
    args = parser.parse_args()
    port = args.port
    host = args.host
    _fmu_folder = args.folder
    print(f"Using FMU folder: {_fmu_folder}")

    serve(host="0.0.0.0", port=port)