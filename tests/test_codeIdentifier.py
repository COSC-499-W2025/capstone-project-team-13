# --- test_codeIdentifier.py ---

import os
import tempfile
import textwrap
import os
import sys
import unittest

# Ensure the project's src directory is on sys.path so tests can import codeIdentifier
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src")))

from Analysis.codeIdentifier import identify_language_and_framework


def _write_temp(text, ext):
    fd, path = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(text))
    return path


class TestCodeIdentifier(unittest.TestCase):

    def test_python_django(self):
        path = _write_temp("""
            from django.shortcuts import render
        """, ".py")
        lang, fw = identify_language_and_framework(path)
        self.assertEqual(lang, "Python")
        self.assertEqual(fw, ["Django"])

    def test_python_flask(self):
        path = _write_temp("""
            from flask import Flask
        """, ".py")
        lang, fw = identify_language_and_framework(path)
        self.assertEqual(lang, "Python")
        self.assertEqual(fw, ["Flask"])

    def test_js_react(self):
        path = _write_temp("""
            import React from 'react'
            const x = 1
        """, ".js")
        lang, fw = identify_language_and_framework(path)
        self.assertEqual(lang, "JavaScript")
        self.assertEqual(fw, ["React"])

    def test_unknown_framework_python(self):
        path = _write_temp("""
            print("hello")
        """, ".py")
        lang, fw = identify_language_and_framework(path)
        self.assertEqual(lang, "Python")
        self.assertEqual(fw, [])

    def test_unknown_extension(self):
        path = _write_temp("""
            some random text
        """, ".txt")
        lang, fw = identify_language_and_framework(path)
        self.assertIsNone(lang)
        self.assertIsNone(fw)

    def test_typescript_angular(self):
        path = _write_temp("""
            import { Component } from '@angular/core';
        """, ".ts")
        lang, fw = identify_language_and_framework(path)
        self.assertEqual(lang, "TypeScript")
        self.assertEqual(fw, ["Angular"])


if __name__ == '__main__':
    unittest.main()