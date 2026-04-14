"""Gradio UI for the Logistics AI Agent.

Run:
    python -m src.ui.gradio_app
Requires the MCP server to be running:
    python -m src.mcp_server.server
"""

import uuid

import gradio as gr

from src.agent.agent import LogisticsAgent

# --------------------------------------------------------------------------- helpers

EXAMPLES = [
    "Cherche le client Dupont",
    "Donne-moi les chargements en cours pour le client CLT-001",
    "Quel est le statut du chargement CHG-2026-00893 ?",
    "Y a-t-il des chargements en retard ?",
    "Liste tous les chargements livrés cette semaine",
]


async def _send(message: str, history: list, session_id: str):
    if not message.strip():
        return history, "", gr.update()

    agent = LogisticsAgent(session_id=session_id)
    response = await agent.chat(message)

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": response},
    ]
    return history, "", response


# --------------------------------------------------------------------------- layout

with gr.Blocks(title="Logistics AI Agent") as demo:

    session_state = gr.State(value=lambda: str(uuid.uuid4()))

    gr.Markdown(
        "# Logistics AI Agent\n"
        "Interrogez les clients et les chargements en langage naturel."
    )

    with gr.Row(equal_height=False):

        # -------------------------------------------------- left: chat history
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                value=[],
                label="Conversation",
                height=480,
                show_label=True,
                render_markdown=True,
            )

            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ex : Trouve le client Dupont et ses chargements en cours…",
                    scale=5,
                    show_label=False,
                    lines=2,
                )
                send_btn = gr.Button(
                    "Envoyer ➤",
                    variant="primary",
                    scale=1,
                )

            gr.Examples(
                examples=EXAMPLES,
                inputs=msg_input,
                label="Exemples de questions",
            )

        # ------------------------------------------ right: formatted response
        with gr.Column(scale=2):
            gr.Markdown("### Dernière réponse")
            response_pane = gr.Markdown(
                value="*La réponse s'affichera ici…*",
            )
            clear_btn = gr.Button("Effacer la conversation", variant="secondary", size="sm")

    # ----------------------------------------------------------------------- events

    send_btn.click(
        _send,
        inputs=[msg_input, chatbot, session_state],
        outputs=[chatbot, msg_input, response_pane],
    )

    msg_input.submit(
        _send,
        inputs=[msg_input, chatbot, session_state],
        outputs=[chatbot, msg_input, response_pane],
    )

    def _clear():
        return [], "", "*La réponse s'affichera ici…*"

    clear_btn.click(_clear, outputs=[chatbot, msg_input, response_pane])


# --------------------------------------------------------------------------- entrypoint

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
    )
