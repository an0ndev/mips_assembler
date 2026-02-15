from abc import abstractmethod
from typing import Optional

FieldName = str
FieldValue = int
MachineCodeFields = dict[FieldName, FieldValue]


class Field:
    @staticmethod
    @abstractmethod
    def parse(text: str) -> MachineCodeFields:
        return {}


class Imm(Field):
    @staticmethod
    def parse(text: str) -> MachineCodeFields:
        if text.startswith("0x"):
            text = text[2:]
            if len(text) % 2 == 1:
                text = text.zfill(len(text) + 1)
            val = int.from_bytes(bytes.fromhex(text), byteorder="big")
        elif text.startswith("0b") or text.startswith("2_"):
            text = text[2:]
            text = text.replace("_", "").replace(" ", "")
            assert len(text) <= 16, f"bitstring literal {text} too long for 16-bit field"
            val = 0
            power = 0
            for bit in reversed(text):
                assert bit in ("0", "1"), f"invalid bitstring character {bit}"
                if bit == "1":
                    val += (2 ** power)
                power += 1
        else:
            try:
                val = int(text)
            except ValueError:
                assert False, f"Invalid immediate {text}"
            if val < 0:
                assert val >= -(2 ** 15), f"immediate of {val} cannot fit in the field"
                as_bytes = val.to_bytes(length=2, byteorder="big", signed=True)
                val = int.from_bytes(as_bytes, byteorder="big", signed=False)
        return {"imm": val}


def _reg_name_to_number(reg_name: str) -> int:
    if reg_name == "at":
        return 1
    if reg_name == "gp":
        return 28
    if reg_name == "sp":
        return 29
    if reg_name == "fp":
        return 30
    if reg_name == "ra":
        return 31
    # why are T registers disjoint??
    if reg_name == "t8":
        return 24
    if reg_name == "t9":
        return 25

    groups = {"v": 2, "a": 4, "t": 8, "s": 16, "k": 26}

    for name, start_off in groups.items():
        if reg_name.startswith(name):
            return start_off + int(reg_name[len(name):])

    assert False, f"invalid register name {reg_name}"


def _reg_spec_to_number(text: str) -> int:
    assert text.startswith("$"), f"Register spec {text} did not start with $"
    value = text[1:]

    try:
        int(value)
        is_reg_num = True
    except ValueError:
        is_reg_num = False

    if is_reg_num:
        return int(value)
    else:
        return _reg_name_to_number(value)


class Register(Field):
    field_name: str

    @classmethod
    def parse(cls, text: str):
        return {cls.field_name: _reg_spec_to_number(text)}


class Offset(Field):
    register_field_name: str

    @classmethod
    def parse(cls, text: str):
        imm_part, sep, reg_part = text.rpartition("(")
        reg_part = reg_part[:-1]  # remove ")"
        if len(imm_part) == 0:
            imm_part = "0"
        return {cls.register_field_name: _reg_spec_to_number(reg_part), **Imm.parse(imm_part)}


class OffsetRs(Offset):
    register_field_name = "rs"


class Rt(Register):
    field_name = "rt"


class Rs(Register):
    field_name = "rs"


class Rd(Register):
    field_name = "rd"


class Instruction:
    name = "TODO"
    opcode = 0
    format: list[Field] = []

    @staticmethod
    def to_bytes(instr):
        return instr.to_bytes(length=4, byteorder="big")

    @classmethod
    def _base_val(cls, rs: int = 0, rt: int = 0) -> int:
        """Generate instruction skeleton with common fields populated."""
        return ((cls.opcode << 10) | (rs << 5) | rt) << 16

    @classmethod
    @abstractmethod
    def encode(cls, **kwargs) -> bytes:
        return b""


class RType(Instruction):
    opcode: int
    funct: int = 0

    @classmethod
    def encode(cls, rs: int = 0, rt: int = 0, rd: int = 0, sh_amt: int = 0) -> bytes:
        instr = cls._base_val(rs=rs, rt=rt)

        instr |= rd << 11
        instr |= sh_amt << 6
        instr |= cls.funct

        return Instruction.to_bytes(instr)


class IType(Instruction):
    @classmethod
    def encode(cls, rs: int = 0, rt: int = 0, imm: int = 0) -> bytes:
        instr = cls._base_val(rs=rs, rt=rt)
        top_bytes = (instr >> 16).to_bytes(length=2, byteorder="big")

        assert imm <= 2 ** 16 - 1, f"immediate of {imm} cannot fit in the field"

        imm_bytes = imm.to_bytes(length=2, byteorder="big", signed=False)

        return top_bytes + imm_bytes


class Addi(IType):
    name = "addi"
    format = [Rt, Rs, Imm]
    opcode = 0b001000


class Andi(IType):
    name = "andi"
    format = [Rt, Rs, Imm]
    opcode = 0b001100


class Ori(IType):
    name = "ori"
    format = [Rt, Rs, Imm]
    opcode = 0b001101


class Xori(IType):
    name = "xori"
    format = [Rt, Rs, Imm]
    opcode = 0b001110


class Sw(IType):
    name = "sw"
    format = [Rt, OffsetRs]
    opcode = 0b101011


class Lw(IType):
    name = "lw"
    format = [Rt, OffsetRs]
    opcode = 0b100011


class Multu(RType):
    name = "multu"
    format = [Rd, Rs, Rt]
    funct = 0b011001


class Sll(RType):
    name = "sll"
    format = [Rd, Rt, Rs]
    funct = 0b000000


class Sra(RType):
    name = "sra"
    format = [Rd, Rt, Rs]
    funct = 0b000011


class Srl(RType):
    name = "srl"
    format = [Rd, Rt, Rs]
    funct = 0b000010


class Add(RType):
    name = "add"
    format = [Rd, Rs, Rt]
    funct = 0b100000


class Sub(RType):
    name = "sub"
    format = [Rd, Rs, Rt]
    funct = 0b100010


class And(RType):
    name = "and"
    format = [Rd, Rs, Rt]
    funct = 0b100100


class Or(RType):
    name = "or"
    format = [Rd, Rs, Rt]
    funct = 0b100101


class Xor(RType):
    name = "xor"
    format = [Rd, Rs, Rt]
    funct = 0b100110


class Nop(Sll):
    name = "nop"
    format = []


instruction_types = [Addi, Andi, Ori, Xori, Sw, Lw, Multu, Sll, Sra, Srl, Add, Sub, And, Or, Xor, Nop]


nop_machine_code = b"\x00\x00\x00\x00"


def assemble(source_lines: list[str], **settings) -> tuple[list[tuple[bytes, Optional[str]]], str]:
    settings.setdefault("add_nops", False)
    settings.setdefault("as_vhdl", False)
    settings.setdefault("byte_addressed", False)

    instructions = []

    for line in source_lines:
        try:
            instr, comment = assemble_line(line)
        except AssertionError as assertion_error:
            raise AssertionError(str(assertion_error) + f" (offending instruction: {line})")
        if len(instr) > 0:
            instructions.append((instr, line))

        if comment is not None and comment.startswith("pragma"):
            directive = comment.partition(" ")[2]
            if directive == "nops_on":
                settings["add_nops"] = True
            elif directive == "nops_off":
                settings["add_nops"] = False
            else:
                assert False, f"unknown assembler directive {directive}"

    if settings["add_nops"]:
        instrs_with_nops = []
        for instr, line in instructions:
            instrs_with_nops.append((instr, line))
            if instr != nop_machine_code:
                for _ in range(4):
                    instrs_with_nops.append((nop_machine_code, None))

        instructions = instrs_with_nops

    if settings["as_vhdl"]:
        code_text = machine_code_to_vhdl(instructions, byte_addressed=settings["byte_addressed"])
    else:
        code_text = machine_code_to_text(instructions)

    return instructions, code_text


def assemble_line(line: str) -> (bytes, Optional[str]):
    line = line.strip()

    if line == "":
        return b"", None
    if line.startswith(";"):
        return b"", line.partition(";")[2].strip()

    instr_name, _, operands = line.partition(" ")

    matching_instr_types = list(filter(
        lambda possible_type: possible_type.name == instr_name,
        instruction_types
    ))
    if len(matching_instr_types) == 0:
        assert False, f"Unknown mnemonic {instr_name}"
    assert len(matching_instr_types) == 1, \
        f"Internal error: multiple instruction types registered with name {instr_name}"
    instr_type = matching_instr_types[0]

    if len(instr_type.format) > 0:
        operands = list(map(lambda s: s.strip(), operands.split(",")))
        operands = operands[:len(instr_type.format)]
        # remove comment from last operand (at end of line)
        if ";" in operands[-1]:
            comment = operands[1].partition(";")[2].strip()
            operands[-1] = operands[-1].split(";")[0].strip()
        else:
            comment = None

        if len(operands) < len(instr_type.format):
            assert False,\
                f"instruction {instr_name} needs {len(instr_type.format)} operands"

        parsed_operands = {}
        for operand_parser, raw_operand in zip(instr_type.format, operands):
            parsed_operands = {**parsed_operands, **operand_parser.parse(raw_operand)}
    else:
        if ";" in operands:
            comment = operands.partition(";")[2].strip()
            operands = operands.partition(";")[0].strip()
        else:
            comment = None
        assert operands.strip() == "", f"Did not expect operands for {instr_name}"
        parsed_operands = {}

    encoded_instr = instr_type.encode(**parsed_operands)
    return encoded_instr, comment


def machine_code_to_vhdl(machine_code: list[tuple[bytes, Optional[str]]], byte_addressed: bool) -> str:
    text = ""

    for instr, src_line in machine_code:
        instr_hex = instr.hex().upper()

        text += "    " * 2

        if byte_addressed:
            for start_idx in range(4):
                byte = instr_hex[start_idx * 2:(start_idx + 1) * 2]
                text += f"x\"{byte}\","
                if start_idx < 3:
                    text += " "
        else:
            text += f"x\"{instr_hex}\","

        if src_line is not None:
            text += " -- " + src_line.strip()

        text += "\n"

    text = text[:-1]  # remove trailing newline

    return text


def machine_code_to_text(machine_code: list[tuple[bytes, Optional[str]]]) -> str:
    lines = []

    for instr, src_line in machine_code:
        lines.append(instr.hex())

    return "\n".join(lines)


# UI

def run_ui():
    import tkinter
    import tkinter.messagebox
    import traceback

    root = tkinter.Tk()
    root.title("MIPS Assembler, by Eric Reed (ejr9567@g.rit.edu)")

    assembly_label = tkinter.Label(root, text="Assembly")
    assembly_label.grid(row=1, columnspan=2)
    assembly_box = tkinter.Text(root, height=20)
    assembly_box.grid(row=2, column=0)
    assembly_box_scrollbar = tkinter.Scrollbar(root, command=assembly_box.yview)
    assembly_box_scrollbar.grid(row=2, column=1, sticky="NS")
    assembly_box["yscrollcommand"] = assembly_box_scrollbar.set

    def assemble_button_handler():
        lines = assembly_box.get("1.0", "end").split("\n")

        options = {
            "add_nops": add_nops_var.get(),
            "as_vhdl": as_vhdl_var.get()
        }

        try:
            _, code_text = assemble(lines, **options)
        except AssertionError as assertion_error:
            code_text = "Syntax error: " + str(assertion_error)
        except Exception:
            code_text = "Unexpected error:\n" + traceback.format_exc()

        machine_code_box.delete("1.0", "end")
        machine_code_box.insert("1.0", code_text)

    def paste_input():
        assembly_box.delete("1.0", "end")
        assembly_box.insert("1.0", root.clipboard_get())

    def copy_output():
        root.clipboard_clear()
        root.clipboard_append(machine_code_box.get("1.0", "end"))

    settings_frame = tkinter.Frame(root)

    assemble_button = tkinter.Button(settings_frame, text="Assemble", command=assemble_button_handler)
    assemble_button.grid(row=0, column=0)

    add_nops_var = tkinter.BooleanVar(value=True)
    with_nops_checkbutton = tkinter.Checkbutton(settings_frame, variable=add_nops_var, text="Insert NOPs")
    with_nops_checkbutton.grid(row=1, column=0)

    as_vhdl_var = tkinter.BooleanVar(value=True)
    as_vhdl_checkbutton = tkinter.Checkbutton(settings_frame, variable=as_vhdl_var, text="As VHDL")
    as_vhdl_checkbutton.grid(row=2, column=0)

    settings_frame.grid(row=1, rowspan=2, column=2)

    machine_code_label = tkinter.Label(root, text="Machine code")
    machine_code_label.grid(row=1, column=3, columnspan=2)

    machine_code_box = tkinter.Text(root, height=20)
    machine_code_box.grid(row=2, column=3)
    machine_code_box_scrollbar = tkinter.Scrollbar(root, command=machine_code_box.yview)
    machine_code_box_scrollbar.grid(row=2, column=4, sticky="NS")
    machine_code_box["yscrollcommand"] = machine_code_box_scrollbar.set

    paste_button = tkinter.Button(root, text="Paste", command=paste_input)
    paste_button.grid(row=3, column=0, columnspan=2)
    copy_button = tkinter.Button(root, text="Copy", command=copy_output)
    copy_button.grid(row=3, column=3, columnspan=2)

    def show_about_text():
        message = """Written by Eric Reed for CMPE-260
Help by Orion Holt, Manuel Waisbord
Contribute at: https://github.com/an0ndev/mips_assembler
Happy assembling! :)"""
        tkinter.messagebox.showinfo("About", message)

    about_button = tkinter.Button(root, text="About", command=show_about_text)
    about_button.grid(row=3, column=2)

    root.mainloop()


if __name__ == '__main__':
    run_ui()
