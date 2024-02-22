# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=line-too-long
import contextlib
import io
import os
import tempfile
import logging

import pytest
import machine
import translator


@pytest.mark.golden_test("tests/hello.yml")
def test_hello_program(golden, caplog):
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        source = os.path.join(tmp_dir_name, "hello_test.txt")
        target = os.path.join(tmp_dir_name, "hello_test.out")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden['source'])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main([source, target])
            machine.main([target, ''])

        with open(target, encoding="utf-8") as file:
            code = file.read()

        assert code == golden.out["code"]
        assert stdout.getvalue() == golden.out["output"]
        assert caplog.text == golden["log"]


@pytest.mark.golden_test("tests/prob5.yml")
def test_prob5_program(golden, caplog):
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        source = os.path.join(tmp_dir_name, "prob5.txt")
        target = os.path.join(tmp_dir_name, "prob5.out")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden['source'])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main([source, target])
            machine.main([target, ''])

        with open(target, encoding="utf-8") as file:
            code = file.read()

        # assert code == golden.out["code"]
        assert stdout.getvalue() == golden.out["output"]
        # assert caplog.text == golden["log"]



@pytest.mark.golden_test("tests/cat.yml")
def test_cat_program(golden, caplog):
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        source = os.path.join(tmp_dir_name, "cat.txt")
        input_stream = os.path.join(tmp_dir_name, "privet_input.txt")
        target = os.path.join(tmp_dir_name, "cat.out")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden['source'])

        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden['input'])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main([source, target])
            machine.main([target, input_stream])

        with open(target, encoding="utf-8") as file:
            code = file.read()

        assert code == golden.out["code"]
        assert stdout.getvalue() == golden.out["output"]
        assert caplog.text == golden["log"]


@pytest.mark.golden_test("tests/hello_user.yml")
def test_hello_user_program(golden, caplog):
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        source = os.path.join(tmp_dir_name, "hello_user_name.txt")
        input_stream = os.path.join(tmp_dir_name, "hello_user_input.txt")
        target = os.path.join(tmp_dir_name, "hello_user_name.out")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden['source'])

        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden['input'])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main([source, target])
            machine.main([target, input_stream])

        with open(target, encoding="utf-8") as file:
            code = file.read()

        assert code == golden.out["code"]
        assert stdout.getvalue() == golden.out["output"]
        assert caplog.text == golden.out["log"]
