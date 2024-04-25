from assemble import assemble


import pathlib
import json
import traceback
import io

import discord

token_json = (pathlib.Path(__file__).parent / "token.txt").read_text()
token = json.loads(token_json)

client = discord.Client()


@client.event
async def on_message(message):
    print(f"message {message}")
    if message.author == client.user:
        return

    msg: str = message.content

    if not msg.startswith("!asm"):
        return

    lines = msg.split("\n")
    command = lines[0]
    options = tuple(map(lambda opt: opt.strip(), command.partition(" ")[2].split(",")))
    src = lines[1:]

    if src[0].startswith("```") and src[-1] == "```":
        src = src[1:-1]

    try:
        _, code_text = assemble(src, add_nops="add_nops" in options, as_vhdl="as_vhdl" in options)
        code_text_with_tags = f"```\n{code_text}\n```"
        as_attachment = len(code_text_with_tags) > 2000
        if not as_attachment:
            code_text = code_text_with_tags
    except AssertionError as assertion_error:
        code_text = "Syntax error: " + str(assertion_error)
        as_attachment = False
    except Exception:
        code_text = "Unexpected error:\n" + "```\n" + traceback.format_exc() + "```"
        as_attachment = False

    if as_attachment:
        args = ("",)
        kwargs = {"file": discord.File(io.BytesIO(code_text.encode()), filename="code.txt")}
    else:
        args = (code_text,)
        kwargs = {}

    await message.reply(*args, **kwargs)


client.run(token)
