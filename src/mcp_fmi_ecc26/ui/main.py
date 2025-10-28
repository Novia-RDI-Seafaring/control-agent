from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, Resource
from pydantic_ai import Agent
from mcp_fmi_ecc26.agent import simulation_agent as agent

import datetime

resource = Resource.create({"service.name": "Ft Otel Streamer Demo"})
provider = TracerProvider(resource=resource)

_fmu_folder = "models/fmus/aarch64-darwin"
from fasthtml.common import *
import sys
sys.path.insert(0, '..')

import fasthtml_otel as ft_otel

# Create FastHTML app
app = FastHTML(exts="ws")
streamer = ft_otel.configure(
    app,
    provider,
    auto_expand_patterns=[],
)

# Instrument Pydantic AI (renderer-agnostic)
ft_otel.instrument_pydantic_ai(provider)

tracer = provider.get_tracer("Ft Otel Streamer Demo")



# Chat messages storage
messages = []

def ChatMessage(idx):
    """Render a chat message."""
    msg = messages[idx]
    bubble = "chat-bubble-primary" if msg["role"] == "user" else "chat-bubble-secondary"
    align = "chat-end" if msg["role"] == "user" else "chat-start"
    return Div(
        Div(msg["role"], cls="chat-header text-xs opacity-70"),
        Div(msg["content"], id=f"chat-content-{idx}", cls=f"chat-bubble {bubble}"),
        id=f"chat-message-{idx}",
        cls=f"chat {align}"
    )

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
async def chat_socket(msg: str, fmu_id: str, send):
    """Handle chat WebSocket messages."""
    print(f"Chat message: {msg}")
    print(f"FMU ID: {fmu_id}")
    tracer = provider.get_tracer("Ft Otel Streamer Demo")
    with tracer.start_as_current_span(f"FMU: {fmu_id.strip()} " + msg.strip()[:10] + "...", attributes={"user_message": msg.strip()}) as span:
        # Add user message
        span.set_attribute("message", msg.strip())
        messages.append({"role": "user", "content": msg.strip()})
        await send(Div(ChatMessage(len(messages) - 1), hx_swap_oob="beforeend", id="chatlist"))
        await send(ChatInput())

        # Process with AI agent
        try:
            with tracer.start_as_current_span("ai_processing") as ai_span:
                ai_span.set_attribute("model", "gpt-4o-mini")
                ai_span.set_attribute("input_length", len(msg))

                result = await agent.run(msg)
                reply = result.response.text

                ai_span.set_attribute("output_length", len(reply))
                ai_span.set_attribute("success", True)

        except Exception as e:
            reply = f"Error: {e} (Check OPENAI_API_KEY environment variable)"
            span.set_attribute("error", True)
            span.set_attribute("error_message", str(e))

        messages.append({"role": "assistant", "content": reply})
        await send(Div(ChatMessage(len(messages) - 1), hx_swap_oob="beforeend", id="chatlist"))

@app.get("/")
def index():
    global _fmu_folder
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
                            Group(Select(
                                *[Option(f, value=f) for f in os.listdir(_fmu_folder)],
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