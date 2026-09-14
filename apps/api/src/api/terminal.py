"""
WebSocket terminal session handler.
Streams interactive shell I/O between xterm.js and the sandbox executor/simulator.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .labs import lab_service

router = APIRouter(tags=["terminal"])


@router.websocket("/ws/terminal/{session_id}")
async def websocket_terminal(websocket: WebSocket, session_id: str):
    await websocket.accept()
    session = lab_service.sandbox_manager.get_session(session_id)

    # Replay scrollback if reconnecting to existing session
    scrollback = session.get_scrollback() if session else ""
    if scrollback:
        formatted_scrollback = scrollback.replace("\n", "\r\n")
        await websocket.send_text(formatted_scrollback)
        await websocket.send_text("\r\n\x1b[32m[Session reconnected]\x1b[0m\r\n")
    else:
        # Initial greeting banner
        banner = (
            "\r\n\x1b[1;36m========================================================\x1b[0m\r\n"
            "\x1b[1;32m  KubeLabs SRE Shell Environment - Live Session\x1b[0m\r\n"
            f"\x1b[33m  Session ID: {session_id} | TTL: 30m\x1b[0m\r\n"
            "\x1b[1;36m========================================================\x1b[0m\r\n\r\n"
        )
        await websocket.send_text(banner)

    await websocket.send_text("sre-engineer@kubelabs-sandbox:~$ ")
    buffer = ""

    try:
        while True:
            data = await websocket.receive_text()

            # Handle Enter key or buffered command ending with Enter
            if data in ["\r", "\n"] or data.endswith("\r") or data.endswith("\n"):
                if data not in ["\r", "\n"]:
                    buffer += data.rstrip("\r\n")
                await websocket.send_text("\r\n")
                cmd = buffer.strip()
                buffer = ""

                if cmd:
                    if cmd == "clear":
                        await websocket.send_text("\x1b[2J\x1b[H")
                    elif cmd == "exit":
                        await websocket.send_text("Closing session.\r\n")
                        break
                    else:
                        # Execute in sandbox
                        res = lab_service.execute_command(session_id, cmd)
                        if res["stdout"]:
                            # Format newlines for PTY
                            out = res["stdout"].replace("\n", "\r\n")
                            await websocket.send_text(out)
                        if res["stderr"]:
                            err = f"\x1b[31m{res['stderr'].replace(chr(10), chr(13) + chr(10))}\x1b[0m"
                            await websocket.send_text(err)

                await websocket.send_text("sre-engineer@kubelabs-sandbox:~$ ")

            # Handle Backspace (\x7f or \x08)
            elif data in ["\x7f", "\x08"]:
                if len(buffer) > 0:
                    buffer = buffer[:-1]
                    await websocket.send_text("\b \b")

            # Handle Ctrl+C
            elif data == "\x03":
                buffer = ""
                await websocket.send_text("^C\r\nsre-engineer@kubelabs-sandbox:~$ ")

            # Standard character input
            else:
                buffer += data
                await websocket.send_text(data)

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        print(f"[Terminal WS] Error: {exc}")
