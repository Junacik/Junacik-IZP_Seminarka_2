#!/usr/bin/python3
#
# Testy pro 2. IZP projekt [2022]
# Autor: - Ramsay#2303
# Zdroj testu: https://github.com/harmim/vut-izp-proj3/tree/master/tests
# Priklady pouziti:
#     python3 ./test.py cluster --valgrind


import argparse
import json
import os
from signal import SIGSEGV
from subprocess import CompletedProcess, run, PIPE
from typing import Dict, List, Tuple, Optional

TEST_LOG_FILENAME = "log.json"
INPUT_FILENAME = "test.in"
VALGRIND_LOG_FILENAME = "valgrind_log.txt"

PASS = "\033[38;5;154m[OK]\033[0m"
FAIL = "\033[38;5;196m[FAIL]\033[0m"
WARNING = "\033[1;33m[WARNING]\033[0m"

BLUE = "\033[38;5;12m"
BOLD = "\033[1m"
END = "\033[0m"

LOREM_IPSUM = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."

BASE_INPUT = [
    ("40", "86", "663"),
    ("43", "747", "938"),
    ("47", "285", "973"),
    ("49", "548", "422"),
    ("52", "741", "541"),
    ("56", "44", "854"),
    ("57", "795", "59"),
    ("61", "267", "375"),
    ("62", "85", "874"),
    ("66", "125", "211"),
    ("68", "80", "770"),
    ("72", "277", "272"),
    ("74", "222", "444"),
    ("75", "28", "603"),
    ("79", "926", "463"),
    ("83", "603", "68"),
    ("86", "238", "650"),
    ("87", "149", "304"),
    ("89", "749", "190"),
    ("93", "944", "835"),
]

RANDOM_TEXT_INPUT = [(LOREM_IPSUM,)]

WRONG_COUNT_INPUT = [("1", "1", "")]

WRONG_ID_INPUT_1 = [("xx", "1", "2")]

WRONG_ID_INPUT_2 = [("3.15", "1", "2")]

WRONG_COORDINATE_INPUT_1 = [("1", "1", "1"), ("2", "xx", "2")]

WRONG_COORDINATE_INPUT_2 = [("1", "1", "1"), ("2", "3.15", "2")]

COORDINATE_OUT_OUF_RANGE_INPUT_1 = [("1", "-1000", "2")]

COORDINATE_OUT_OUF_RANGE_INPUT_2 = [("1", "2000", "2")]

NON_UNIQUE_ID_INPUT = [("1", "1", "2"), ("1", "4", "8")]

MULITPLE_OBJECTS_INPUT = [("1", "1", "2", "3", "4", "5")]

OUTPUT_1 = [(i + 1,) for i in range(20)]

OUTPUT_2 = [
    (1, 6, 9, 11, 14, 17),
    (2,),
    (3,),
    (4,),
    (5, 15),
    (7, 16, 19),
    (8, 10, 12, 13, 18),
    (20,),
]

OUTPUT_3 = [tuple(i + 1 for i in range(20))]

OUTPUT_4 = [(1,)]


class Tester:
    def __init__(
        self,
        program_name: str,
        save_logs_file: bool,
        valgrind_enabled: bool,
        stop_on_error: bool,
    ) -> None:
        self.program_name = "./" + program_name
        self.test_count = 0
        self.pass_count = 0
        self.logs: List[Dict] = []
        self.valgrind_enabled = valgrind_enabled
        self.stop_on_error = stop_on_error
        self.save_logs_file = save_logs_file

    def test(
        self,
        test_name: str,
        args: List[str],
        filename: Optional[str],
        input_: List[Tuple[str, str]],
        expected_contacts: Optional[List[int]] = None,
        should_fail: bool = False,
        check_crash: bool = False,
        create_file: bool = True,
        count: Optional[int] = None,
    ):
        self.test_count += 1
        failed = False
        error_msg: str = ""

        if filename is not None and create_file:
            self.create_input_file(input_, filename, count)

        str_output = (
            self.create_output(input_, expected_contacts)
            if expected_contacts is not None
            else ""
        )

        p: CompletedProcess[str]

        try:
            all_args = []
            if filename is not None:
                all_args += [filename] + args
            else:
                all_args += args

            p = run(
                [self.program_name] + all_args,
                stdout=PIPE,
                stderr=PIPE,
                encoding="ascii",
            )
        except UnicodeEncodeError as e:
            self.print_fail(test_name)
            print("Vystup obsahuje znaky ktere nepatri do ASCII (napr. diakritika)")
            print(e)
        except Exception as e:
            self.print_fail(test_name)
            print("Chyba pri volani programu")
            print(e)
            exit(1)

        if p.returncode != 0:
            if p.returncode == -SIGSEGV and check_crash:
                failed = True
                error_msg += f"Program neocekavane spadl s navratovym kodem {p.returncode}. Pravdepodobne sahas do pameti ktera neni tvoje\n"
            elif not should_fail and not check_crash:
                failed = True
                error_msg += f"Program vratil chybovy navratovy kod {p.returncode} prestoze nemel\n"

        else:
            if should_fail:
                failed = True
                error_msg += "Program byl uspesne ukoncen, i presto ze nemel byt\n"

        if (
            not self.assert_equal(str_output, p.stdout)
            and not should_fail
            and not check_crash
        ):
            failed = True
            error_msg += "Vystup programu se neshoduje s ocekavanym vystupem"

        if should_fail and len(p.stderr) == 0:
            failed = True
            error_msg += "Program nevratil chybovou hlasku na STDERR\n"

        valgrind_out = ""
        if self.valgrind_enabled and (valgrind_out := self.check_memory(all_args)):
            failed = True

        if failed:
            self.print_fail(test_name)
            print(error_msg)
            print(f"{self.bold('Argumenty')}: {' '.join(all_args)}")
            print(f"{self.bold('Predpokladany vystup')}:")
            print(self.debug(str_output))
            print(f"{self.bold('STDOUT')}:")
            print(self.debug(p.stdout))
            print(f"{self.bold('STDERR')}:")
            print(self.debug(p.stderr))

            if valgrind_out:
                print(f"{self.bold('Valgrind')}:")
                print(self.debug(valgrind_out))

        else:
            self.pass_count += 1
            self.print_pass(test_name)

        input_file_content = ""
        try:
            input_file_content = open(f"./{INPUT_FILENAME}").read()
        except Exception as e:
            pass

        data = {
            "test_name": test_name,
            "status": "failed" if failed else "ok",
            "error_message": error_msg,
            "args": " ".join(all_args),
            "file_content": input_file_content,
            "exptected_output": str_output,
            "stdout": p.stdout,
            "stderr": p.stderr,
            "return_code": p.returncode,
            "valgrind": valgrind_out,
        }

        self.test_cleanup()
        self.logs.append(data)

        if failed and self.stop_on_error:
            self.valgrind_cleanup()

            if self.save_logs_file:
                t.save_logs()

            t.print_stats()

            exit(1)

    def check_memory(self, args: List[str]) -> str:
        try:
            run(
                [
                    "valgrind",
                    "--leak-check=full",
                    "--track-origins=yes",
                    "--quiet",
                    f"--log-file={VALGRIND_LOG_FILENAME}",
                    self.program_name,
                ]
                + args,
                stdout=PIPE,
                stderr=PIPE,
            )
        except Exception as e:
            self.print_fail("Neporadilo se spustit valgrind")
            print(self.debug(e))
            self.valgrind_cleanup()
            return ""

        try:
            with open(VALGRIND_LOG_FILENAME, encoding="utf8", mode="r") as f:
                valgrind_out = f.read()
                return valgrind_out
        except Exception as e:
            self.print_fail("Neporadilo se precist valgrind log")
            print(self.debug(e))
            self.valgrind_cleanup()
            return ""

    def print_stats(self) -> None:
        success_rate = self.pass_count / self.test_count * 100
        print(
            self.bold(
                f"Uspesnost: {success_rate:.2f} % [{self.pass_count} / {self.test_count}]"
            )
        )

    def create_input_file(
        self,
        input_: List[Tuple[str, str, str]],
        filename: str,
        count: Optional[str] = None,
    ) -> None:
        if count is None:
            count = str(len(input_))

        out = f"count={count}\n"

        for line in input_:
            for item in line:
                out += f"{item} "

            out = out[:-1]
            out += "\n"

        with open(f"./{filename}", encoding="utf8", mode="w") as f:
            f.write(out)

    def assert_equal(self, output: str, expected_output: str) -> bool:
        lines = {line.lower() for line in expected_output.rstrip().split("\n")}

        for line in output.rstrip().split("\n"):
            line = line.lower()

            if line not in lines:
                return False

        return True

    def create_output(
        self,
        input_: List[Tuple[str, str, str]],
        exptected_contacts: List[Tuple[int, ...]],
    ) -> str:
        out = "Clusters:\n"

        for idx, cluster in enumerate(exptected_contacts):
            out += f"cluster {idx}: "
            for obj_idx in cluster:
                obj_id, x, y = input_[obj_idx - 1]

                out += f"{obj_id}[{x},{y}] "

            out = out[:-1]
            out += "\n"

        out = out[:-1]
        return out

    def save_logs(self) -> None:
        with open(TEST_LOG_FILENAME, "w", encoding="utf8") as f:
            json.dump(self.logs, f, indent=4)

    @staticmethod
    def test_cleanup() -> None:
        try:
            os.remove(f"./{INPUT_FILENAME}")
        except Exception:
            pass

    @staticmethod
    def valgrind_cleanup() -> None:
        try:
            os.remove(f"./{VALGRIND_LOG_FILENAME}")
        except Exception:
            pass

    @staticmethod
    def debug(text: str) -> str:
        return f"{BLUE}{text}{END}"

    @staticmethod
    def warning(text: str) -> str:
        return f"{WARNING}{text}{END}"

    @staticmethod
    def bold(text: str) -> str:
        return f"{BOLD}{text}{END}"

    @staticmethod
    def print_fail(msg: str) -> None:
        print(FAIL, msg)

    @staticmethod
    def print_pass(msg: str) -> None:
        print(PASS, msg)

    @staticmethod
    def detect_valgrind():
        try:
            run(["valgrind"], stdout=PIPE, stderr=PIPE)
            return True
        except:
            print(
                Tester.warning(
                    "Valgrind neni nainstalovan, pro kontrolu memory leaku nainstalujte valgrind"
                )
            )
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tester 2. IZP projektu [2022]")
    parser.add_argument(
        "program_name",
        metavar="PROGRAM_NAME",
        type=str,
        help="Cesta k programu (napriklad: ./cluster)",
    )
    parser.add_argument(
        "--save-logs",
        dest="save_logs",
        action="store_true",
        help="Zapne ukladani logu do souboru",
    )

    parser.add_argument(
        "--valgrind",
        dest="valgrind_enabled",
        action="store_true",
        help="Zapne kontrolu prace s pameti pomoci valgrindu",
    )

    parser.add_argument(
        "--stop-on-error",
        dest="stop_on_error",
        action="store_true",
        help="Testovani programu se prerusi pri vyskytu chyby",
    )

    args = parser.parse_args()

    t = Tester(
        args.program_name, args.save_logs, args.valgrind_enabled, args.stop_on_error
    )

    t.test_cleanup()

    t.test(
        "Test ze zadani #1",
        ["20"],
        INPUT_FILENAME,
        BASE_INPUT,
        OUTPUT_1,
        create_file=True,
    )
    t.test(
        "Test ze zadani #2",
        ["8"],
        INPUT_FILENAME,
        BASE_INPUT,
        OUTPUT_2,
        create_file=True,
    )
    t.test(
        "Test ze zadani #3",
        [],
        INPUT_FILENAME,
        BASE_INPUT,
        OUTPUT_3,
        create_file=True,
    )

    t.test(
        "Test parametru N #1",
        ["xx"],
        INPUT_FILENAME,
        BASE_INPUT,
        None,
        should_fail=True,
        create_file=True,
    )

    t.test(
        "Test parametru N #2",
        ["2.10"],
        INPUT_FILENAME,
        BASE_INPUT,
        None,
        should_fail=True,
        create_file=True,
    )

    t.test(
        "Test neznamych parametru #1",
        ["2", "xx", "yy"],
        INPUT_FILENAME,
        BASE_INPUT,
        None,
        should_fail=True,
        create_file=True,
    )

    t.test(
        "Test chybejiciho nazvu souboru #1",
        [],
        None,
        BASE_INPUT,
        None,
        should_fail=True,
    )

    t.test(
        "Test neexistujiciho souboru #1",
        ["1"],
        INPUT_FILENAME,
        BASE_INPUT,
        None,
        should_fail=True,
        create_file=False,
    )

    t.test(
        "Test nahodneho textu #1",
        [],
        INPUT_FILENAME,
        RANDOM_TEXT_INPUT,
        [],
        create_file=True,
        should_fail=True,
        count=LOREM_IPSUM,
    )

    t.test(
        "Test parametru count #1",
        ["1"],
        INPUT_FILENAME,
        BASE_INPUT,
        OUTPUT_3,
        create_file=True,
        should_fail=True,
        count="30",
    )

    t.test(
        "Test parametru count #2",
        ["1"],
        INPUT_FILENAME,
        BASE_INPUT,
        OUTPUT_4,
        create_file=True,
        count="1",
    )

    t.test(
        "Test parametru count #3",
        ["1"],
        INPUT_FILENAME,
        WRONG_COUNT_INPUT,
        [],
        create_file=True,
        should_fail=True,
        count="-100",
    )

    t.test(
        "Test vice objektu na radku #1",
        ["1"],
        INPUT_FILENAME,
        MULITPLE_OBJECTS_INPUT,
        None,
        create_file=True,
        should_fail=True,
    )

    t.test(
        "Test ID neni cislo #1",
        ["1"],
        INPUT_FILENAME,
        WRONG_ID_INPUT_1,
        None,
        create_file=True,
        should_fail=True,
    )

    t.test(
        "Test ID neni cele cislo #1",
        ["1"],
        INPUT_FILENAME,
        WRONG_ID_INPUT_2,
        None,
        create_file=True,
        should_fail=True,
    )

    t.test(
        "Test souradnice neni cislo #1",
        ["1"],
        INPUT_FILENAME,
        WRONG_COORDINATE_INPUT_1,
        None,
        create_file=True,
        should_fail=True,
    )

    t.test(
        "Test souradnice neni cele cislo #2",
        ["1"],
        INPUT_FILENAME,
        WRONG_COORDINATE_INPUT_2,
        None,
        create_file=True,
        should_fail=True,
    )

    t.test(
        "Test souradnice je mimo rozsah #1",
        ["1"],
        INPUT_FILENAME,
        COORDINATE_OUT_OUF_RANGE_INPUT_1,
        None,
        create_file=True,
        should_fail=True,
    )

    t.test(
        "Test souradnice je mimo rozsah #2",
        ["1"],
        INPUT_FILENAME,
        COORDINATE_OUT_OUF_RANGE_INPUT_2,
        None,
        create_file=True,
        should_fail=True,
    )

    t.test(
        "Test ID neni unikatni #1",
        ["1"],
        INPUT_FILENAME,
        NON_UNIQUE_ID_INPUT,
        None,
        create_file=True,
        should_fail=True,
    )

    if args.save_logs:
        t.save_logs()

    t.print_stats()
    t.valgrind_cleanup()