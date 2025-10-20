from rake_nltk import Rake
import nltk
from pathlib import Path
from typing import Union

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
    """Read the contents of a code file and return it as a string."""
    with open(filepath, 'r', encoding='utf-8') as file:
        code_text = file.read()
    return code_text

def extract_code_keywords_with_scores(filepath: Union[str, Path]) -> list[tuple[float, str]]:
    """
    Read code from a filepath and extract keywords and their scores using RAKE
    with the custom CODE_STOPWORDS.

    Args:
        filepath (Union[str, Path]): Path to the code file.

    Returns:
        list[tuple[float, str]]: A list of (score, keyword) pairs, sorted by importance.
    """
    text = read_code_file(str(filepath))
    r = Rake(stopwords=CODE_STOPWORDS)
    r.extract_keywords_from_text(text)
    return r.get_ranked_phrases_with_scores()


