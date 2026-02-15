from assemble import assemble


import pathlib
import json
import traceback
import io

import discord

token_json = (pathlib.Path(__file__).parent / "token.txt").read_text()
token = json.loads(token_json)

client = discord.Client()



usage_msg = """Usage:
```
!asm option1,option2,optionN
mmemonic operand,operand,operand
mmemonic operand,operand
mmemonic operand,operand,operand
```

Possible options:
- `add_nops`: insert four NOP instructions after each source instruction, \
forcing the source instruction to propagate through the entire \
pipeline before the next instruction starts executing, \
thereby preventing read-after-write hazards
- `as_vhdl`: generate the result as the contents of a VHDL `constant`, i.e. \
the instruction memory contents
- `byte_addressed`: with `as_vhdl`, generates the VHDL code for a byte-addressed \
instruction memory, i.e. each where entry in the memory array is \
defined as (7 downto 0), as opposed to the default assumption \
of word-addressed instruction memory

Example:
```
!asm add_nops,as_vhdl

; Get switches' value
; (read from addr 1022)
lw $t1, 0x3fe($0)

; Isolate lowest switch value
; (bitwise AND with 0x1)
addi $t2, $0, 0x1
and $t1, $t1, $t2

; Calculate value to display
; on seven-seg display as
; 7 if switch on, else 6
addi $t0, $t1, 6   ; value = 6 + switch

; Display 6 or 7 on seven-seg
; (write to addr 1023)
sw $t0, 0x3ff($0)
```

For help or improvements, contact Eric. Thanks!

*For a list of instructions and their encodings, see [the Google Sheet](https://docs.google.com/spreadsheets/d/1pI6MH3ZraE8Q-X83HXcNkxj-OpqjiBincxFQDggws80/edit?gid=1318169272#gid=1318169272):*
"""

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    async def reply_if_dm(*args, **kwargs):
        if message.channel.type == discord.ChannelType.private:
            await message.reply(*args, **kwargs)

    msg: str = message.content
    if message.channel.type == discord.ChannelType.private:
        print(f"DM from {message.author.name}:\n{msg}\n")

    if msg.startswith("!help"):
        await reply_if_dm(usage_msg)
        return

    if not msg.startswith("!asm"):
        await reply_if_dm("bad command :( type !help for help")
        return

    lines = msg.split("\n")
    if len(lines) < 2:
        await reply_if_dm("need the command line and several lines of code :( type !help for help")
        return

    command_line = lines[0]
    if " " not in command_line:
        command_name = command_line
        options = ""
    else:
        command_name, _, options = command_line.partition(" ")

    options = options.split(",")
    if len(options) == 1 and options[0] == "":
        options = []
    options = list(map(lambda s: s.strip(), options))

    # await reply_if_dm(f"`command: {command_name}, options: {options}`")

    if command_name != "!asm":
        await reply_if_dm(f"unexpected command {command_name} :( only supports !asm. type !help for help")
        return

    src = lines[1:]

    while src[0].strip() == "":
        src = src[1:]

    if src[0].startswith("```") and src[-1] == "```":
        src = src[1:-1]

    try:
        _, code_text = assemble(src, add_nops="add_nops" in options, as_vhdl="as_vhdl" in options, byte_addressed="byte_addressed" in options)
        code_text_with_tags = f"```\n{code_text}\n```"
        as_attachment = len(code_text_with_tags) > 2000
        if not as_attachment:
            code_text = code_text_with_tags
    except AssertionError as assertion_error:
        code_text = "Syntax error :( " + str(assertion_error)
        as_attachment = False
    except Exception:
        code_text = "Unexpected error :'(\n" + "```\n" + traceback.format_exc() + "```"
        as_attachment = False

    if as_attachment:
        args = ("",)
        kwargs = {"file": discord.File(io.BytesIO(code_text.encode()), filename="code.txt")}
    else:
        args = (code_text,)
        kwargs = {}

    await message.reply(*args, **kwargs)


client.run(token)
