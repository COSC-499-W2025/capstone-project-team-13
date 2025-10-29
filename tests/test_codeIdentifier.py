# --- test_codeIdentifier.py ---

import os
import tempfile
import textwrap
import os
import sys

# Ensure the project's src directory is on sys.path so tests can import codeIdentifier
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src")))

from codeIdentifier import identify_language_and_framework


def test_write_temp(text, ext):
    fd, path = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(text))
    return path


def test_python_django():
    path = _write_temp("""
        from django.shortcuts import render
    """, ".py")
    lang, fw = identify_language_and_framework(path)
    assert lang == "Python"
    assert fw == ["Django"]


def test_python_flask():
    path = _write_temp("""
        from flask import Flask
    """, ".py")
    lang, fw = identify_language_and_framework(path)
    assert lang == "Python"
    assert fw == ["Flask"]


def test_js_react():
    path = _write_temp("""
        import React from 'react'
        const x = 1
    """, ".js")
    lang, fw = identify_language_and_framework(path)
    assert lang == "JavaScript"
    assert fw == ["React"]


def test_unknown_framework_python():
    path = _write_temp("""
        print("hello")
    """, ".py")
    lang, fw = identify_language_and_framework(path)
    assert lang == "Python"
    assert fw == []


def test_unknown_extension():
    path = _write_temp("""
        some random text
    """, ".txt")
    lang, fw = identify_language_and_framework(path)
    assert lang is None
    assert fw is None


def test_typescript_angular():
    path = _write_temp("""
        import { Component } from '@angular/core';
    """, ".ts")
    lang, fw = identify_language_and_framework(path)
    assert lang == "TypeScript"
    assert fw == ["Angular"]