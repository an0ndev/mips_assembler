# MIPS Assembler

Small Discord bot written to assemble MIPS assembly, creating the machine code to be placed into the instruction memory of the MIPS CPU, as created in RIT's CMPE-260 Digital System Design II class.

## Discord bot setup
1. Create a separate Discord account to use for the bot, and join the server(s) you want the bot to work in.

2. Get the token for the Discord account. See https://gist.github.com/MarvNC/e601f3603df22f36ebd3102c501116c6

2. Place the token into a file next to discord_bot.py called token.txt.

(Wrap the token in quotes, since the file is parsed as a JSON string.)

Example contents: `"ABCDEFGHI-TOKEN-goes-here"`

4. Install `discord.py-self` (i.e. `pip install discord.py-self` from a command line)

5. Start the bot: `python discord_bot.py`

## Bot usage

> !asm add_nops,as_vhdl
> 
> addi $1, $0, 5
> 
> addi $2, $0, 6

> (bot responds with result)

- `add_nops` option: places four NOP instructions after each normal instruction. This lets the pipeline of the CPU flush completely, avoiding issues due to a design flaw causing read-after-write hazards.
- `as_vhdl` option: wraps the code VHDL array definition style syntax.

### Registers

You can use the names (i.e. `$t0`) or simply the number of the register you are referencing (ex. `$0`). The number must be in decimal.


### Immediates

Immediates can be in either decimal or hex. If in hex, prepend the value with `0x`. i.e. `10` is equivalent to `0xA`.

Binary immediates are also supported; prepend the value with `0b` or `2_`.

## Bugs
Report to Eric on Discord (@ericmakesbeats), via email (`eric (at) an0n (dot) dev`), or via the issue tracker on GitHub. I will respond fastest to Discord or email. Thanks!
