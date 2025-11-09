from rake_nltk import Rake
import nltk
from pathlib import Path
from typing import Union
import re

nltk.download('punkt')
nltk.download('punkt_tab')

CODE_STOPWORDS = {
    # --- Python / General keywords ---
    'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
    'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global',
    'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass',
    'raise', 'return', 'try', 'while', 'with', 'yield',

    # --- JavaScript keywords ---
    'var', 'let', 'const', 'function', 'new', 'delete', 'switch', 'case',
    'default', 'this', 'super', 'extends', 'implements', 'interface', 'enum',
    'constructor', 'prototype', 'await', 'async', 'typeof', 'instanceof',
    'export', 'import', 'require', 'module', 'package',

    # --- Java / C / C++ keywords ---
    'auto', 'bool', 'boolean', 'break', 'byte', 'catch', 'char', 'class',
    'const', 'constexpr', 'continue', 'default', 'delete', 'do', 'double',
    'else', 'enum', 'extern', 'false', 'final', 'float', 'for', 'friend', 'goto',
    'if', 'inline', 'int', 'long', 'mutable', 'namespace', 'new', 'operator',
    'private', 'protected', 'public', 'register', 'restrict', 'return',
    'short', 'signed', 'sizeof', 'static', 'struct', 'switch', 'template',
    'this', 'throw', 'true', 'try', 'typedef', 'typename', 'union', 'unsigned',
    'using', 'virtual', 'void', 'volatile', 'while',

    # --- Common built-in identifiers / constants ---
    'null', 'none', 'true', 'false', 'self', 'cls', '__init__', '__main__',
    'print', 'input', 'len', 'int', 'float', 'str', 'list', 'dict', 'set',
    'tuple', 'map', 'filter', 'range', 'zip', 'max', 'min', 'sum', 'open',
    'close', 'read', 'write', 'file', 'object',

    # --- Common variable / function naming noise ---
    'temp', 'data', 'info', 'details', 'value', 'item', 'result', 'results',
    'response', 'req', 'res', 'args', 'kwargs', 'param', 'params', 'input',
    'output', 'config', 'options', 'option', 'flag', 'flags', 'count', 'index',
    'idx', 'key', 'keys', 'val', 'vals', 'variable', 'obj', 'objs', 'ref',
    'refs', 'string', 'strings', 'text', 'number', 'numbers', 'element',
    'elements', 'record', 'records', 'node', 'nodes', 'child', 'children',
    'parent', 'file', 'files', 'path', 'dir', 'dirs', 'folder', 'folders',

    # --- Misc programming boilerplate ---
    'main', 'init', 'setup', 'test', 'mock', 'util', 'utils', 'helper',
    'helpers', 'base', 'core', 'common', 'default', 'custom', 'generic',
    'load', 'save', 'update', 'create', 'delete', 'remove', 'edit',
    'add', 'set', 'get', 'put', 'post', 'fetch', 'run', 'exec', 'execute',
    'call', 'func', 'method', 'process', 'handle', 'manager', 'controller',
    'view', 'model', 'service', 'repository', 'repo',

    # --- Symbols to strip ---
    'n', 'i', 'j', 'k', 'x', 'y', 'z', '_', '__', 'a', 'b', 'c'
}

def read_code_file(filepath: str) -> str:
    """Read the contents of a code file and return it as a string, preserving newlines."""
    try:
        with open(filepath, 'r', encoding='utf-8', newline='') as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")
    except PermissionError:
        raise PermissionError(f"Permission denied: {filepath}")
    except UnicodeDecodeError:
        raise ValueError(f"File is not readable as UTF-8 text: {filepath}")




def extract_comments(code: str) -> str:
    """
    Extracts comments from code 
    Keeps each comment distinct to prevent RAKE from merging them.
    """
    if not isinstance(code, str):
        raise TypeError(f"Expected a string of code, got {type(code).__name__}")

    try:
        matches_with_pos = []

        for m in re.finditer(r'//(.*?)$', code, re.MULTILINE):
            matches_with_pos.append((m.start(), m.group(1).strip()))

        for m in re.finditer(r'/\*(.*?)\*/', code, re.DOTALL):
            matches_with_pos.append((m.start(), m.group(1).strip()))

        for m in re.finditer(r'#(.*?)$', code, re.MULTILINE):
            matches_with_pos.append((m.start(), m.group(1).strip()))

        for m in re.finditer(r'"""(.*?)"""', code, re.DOTALL):
            matches_with_pos.append((m.start(), m.group(1).strip()))

        for m in re.finditer(r"'''(.*?)'''", code, re.DOTALL):
            matches_with_pos.append((m.start(), m.group(1).strip()))

        matches_with_pos.sort(key=lambda x: x[0])
        comments = [text for _, text in matches_with_pos if text]
        return ". ".join(comments)

    except re.error as e:
        raise RuntimeError(f"Regex error during comment extraction: {e}")




import os

def extract_code_keywords_with_scores(filepath_or_text: Union[str, Path]) -> list[tuple[float, str]]:
    """
    Accepts either a file path or raw code text, and extracts keywords and their scores using RAKE.

    Args:
        filepath_or_text (Union[str, Path]): Either a valid file path or raw code text.

    Returns:
        list[tuple[float, str]]: A list of (score, keyword) pairs, sorted by importance.
    """
    # Detect whether the input is a path to an existing file
    if isinstance(filepath_or_text, (str, Path)) and os.path.exists(filepath_or_text):
        text = read_code_file(str(filepath_or_text))
    else:
        # Assume it's raw text (already read from file or pasted in)
        text = str(filepath_or_text)

    r = Rake(stopwords=CODE_STOPWORDS)
    text = extract_comments(text)
    r.extract_keywords_from_text(text)
    return r.get_ranked_phrases_with_scores()



