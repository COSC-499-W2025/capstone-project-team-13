from collections import defaultdict, Counter
from pathlib import Path
import re

# --- Top-level skill keywords ---
SKILL_KEYWORDS = {
    # --- Languages (extension-boosted; keywords are import/library names specific to that language) ---
    "Python": [
        "python", "pandas", "numpy", "scipy", "matplotlib", "flask", "django",
        "fastapi", "pytest", "pydantic", "sqlalchemy", "celery", "asyncio",
        "requests", "uvicorn", "gunicorn", "pip", "virtualenv", "poetry",
        "aiohttp", "httpx", "mypy", "typing", "dataclass", "pathlib",
        "beautifulsoup", "scrapy", "pillow", "paramiko", "boto3"
    ],
    "JavaScript": [
        "javascript", "nodejs", "npm", "webpack", "babel", "eslint",
        "axios", "lodash", "jquery", "require", "exports", "promise",
        "callback", "prototype", "yarn", "vite", "parcel", "rollup",
        "esbuild", "nodemon", "pnpm", "commonjs", "module"
    ],
    "TypeScript": [
        "typescript", "tsc", "tsconfig", "interface", "readonly",
        "generics", "enum", "namespace", "typings", "strict",
        "infer", "keyof", "satisfies", "utility types"
    ],
    "Java": [
        "java", "maven", "gradle", "springframework", "spring", "hibernate",
        "junit", "mockito", "lombok", "servlet", "tomcat", "jetty",
        "classpath", "bytecode", "jvm", "jdk", "annotation",
        "extends", "implements", "override", "stream", "optional",
        "pom", "mvn", "intellij"
    ],
    "C/C++": [
        "iostream", "nullptr", "malloc", "cmake", "makefile", "gcc",
        "clang", "sizeof", "typedef", "struct", "printf",
        "scanf", "stdlib", "stdint", "vector", "template",
        "namespace", "stl", "header", "linker", "pointer",
        "cpp", "compile", "executable", "preprocessor"
    ],
    "Rust": [
        "rust", "cargo", "rustc", "crate", "lifetime", "borrow",
        "ownership", "rustup", "tokio", "actix", "serde", "clippy",
        "unwrap", "trait", "impl", "match", "enum", "derive",
        "println", "hashmap", "option", "result"
    ],
    "Go": [
        "golang", "goroutine", "channel", "defer", "panic", "recover",
        "gofmt", "gomod", "gosum", "gopath", "gin", "fiber",
        "cobra", "viper", "grpc", "protobuf", "gorm", "mux"
    ],
    "C#": [
        "csharp", "dotnet", "nuget", "linq", "xamarin", "wpf",
        "blazor", "maui", "aspnet", "nullable", "delegate",
        "event", "lambda", "extension", "attribute", "namespace",
        "interface", "abstract", "sealed", "partial", "async"
    ],
    "Ruby": [
        "ruby", "rails", "gem", "bundler", "rake", "rspec",
        "activerecord", "erb", "sinatra", "gemfile", "rubocop"
    ],
    "PHP": [
        "php", "composer", "laravel", "symfony", "wordpress",
        "artisan", "eloquent", "blade", "phpunit", "namespace"
    ],

    # --- Web and App Development ---
    "Web Development": [
        "html", "css", "javascript", "typescript", "flask", "django",
        "express", "node", "php", "nextjs", "nuxt", "react", "vue",
        "angular", "webpack", "vite", "spa", "ssr", "pwa", "cors",
        "dom", "browser", "frontend", "backend", "fullstack",
        "rest", "graphql", "fetch", "ajax", "websocket"
    ],
    "Frontend Development": [
        "react", "vue", "angular", "svelte", "bootstrap", "tailwind",
        "html", "css", "dom", "jsx", "tsx", "sass", "scss",
        "webpack", "vite", "responsive", "accessibility", "component",
        "props", "state", "hook", "context", "redux", "zustand",
        "emotion", "styled", "animation", "transition"
    ],
    "Backend Development": [
        "flask", "django", "express", "fastapi", "spring", "node",
        "api", "server", "microservices", "rest", "graphql", "grpc",
        "middleware", "endpoint", "route", "controller", "service",
        "repository", "orm", "cache", "queue", "worker"
    ],
    "API Development": [
        "rest", "graphql", "endpoint", "swagger", "postman", "jwt", "oauth",
        "openapi", "webhook", "http", "request", "response",
        "status", "header", "payload", "serialization", "pagination",
        "rate limiting", "api key", "bearer", "token"
    ],
    "Mobile Development": [
        "android", "ios", "flutter", "swift", "kotlin", "react native",
        "expo", "xcode", "apk", "cocoapods", "firebase",
        "push notification", "deep linking", "gesture", "navigation",
        "fragment", "activity", "viewmodel", "jetpack", "compose"
    ],

    # --- Databases ---
    "SQL": [
        "sql", "mysql", "postgresql", "sqlite", "mariadb", "oracle",
        "schema", "foreign key", "primary key", "transaction",
        "stored procedure", "trigger", "view", "aggregate",
        "constraint", "normalization", "acid", "join", "subquery",
        "group by", "order by", "having"
    ],
    "Relational Databases": [
        "sql", "mysql", "postgresql", "sqlite", "oracle", "mariadb",
        "schema", "foreign key", "normalization", "acid", "transaction",
        "constraint", "relation", "primary key", "index"
    ],
    "Non-Relational Databases": [
        "nosql", "mongodb", "redis", "cassandra", "dynamodb",
        "couchdb", "neo4j", "graphdb", "document store", "elasticsearch",
        "firebase", "firestore", "hbase", "memcached", "leveldb",
        "collection", "document", "key value"
    ],
    "Database Management": [
        "orm", "query", "database", "migration", "data model",
        "connection pool", "replication", "backup", "sharding",
        "partitioning", "indexing", "optimization", "alembic",
        "sequelize", "prisma", "mongoose", "typeorm"
    ],

    # --- Data & AI ---
    "Data Science": [
        "numpy", "pandas", "matplotlib", "scipy", "jupyter",
        "notebook", "seaborn", "statsmodels", "sklearn",
        "correlation", "regression", "classification", "clustering",
        "feature", "dataframe", "csv", "eda", "statistics",
        "hypothesis", "distribution", "variance", "covariance"
    ],
    "Machine Learning": [
        "tensorflow", "keras", "pytorch", "sklearn", "xgboost",
        "scikit", "lightgbm", "catboost", "model", "training",
        "prediction", "accuracy", "loss", "gradient", "backpropagation",
        "neural network", "deep learning", "overfitting", "validation",
        "hyperparameter", "epoch", "batch", "optimizer", "learning rate",
        "feature engineering", "cross validation", "confusion matrix"
    ],
    "Data Visualization": [
        "matplotlib", "seaborn", "plotly", "tableau", "dash", "ggplot",
        "bokeh", "altair", "d3", "chart", "plot", "histogram",
        "heatmap", "scatter", "visualization", "dashboard", "figure"
    ],
    "Data Engineering": [
        "airflow", "spark", "hadoop", "etl", "kafka", "pipeline",
        "databricks", "dbt", "snowflake", "bigquery", "redshift",
        "hive", "flink", "beam", "dataflow", "glue", "pyspark",
        "data lake", "data warehouse", "batch processing", "streaming"
    ],

    # --- DevOps / Cloud ---
    "DevOps": [
        "docker", "kubernetes", "jenkins", "ci/cd", "github actions",
        "dockerfile", "compose", "container", "pod", "deployment",
        "terraform", "ansible", "helm", "prometheus", "grafana",
        "nginx", "pipeline", "artifact", "registry", "k8s",
        "gitlab ci", "travis", "circleci", "argocd"
    ],
    "Cloud Computing": [
        "aws", "azure", "gcp", "google cloud", "lambda", "s3", "cloud functions",
        "ec2", "rds", "ecs", "eks", "cloudformation", "iam", "vpc",
        "blob", "cosmos", "app engine", "cloud run", "fargate",
        "serverless", "cdn", "cloudfront", "route53", "elasticbeanstalk"
    ],

    # --- Software Engineering Practices ---
    "Testing & QA": [
        "pytest", "unittest", "selenium", "cypress", "mocha", "jest",
        "test", "mock", "stub", "fixture", "assertion", "coverage",
        "integration test", "unit test", "e2e", "tdd", "bdd",
        "playwright", "vitest", "hypothesis", "faker", "factory",
        "describe", "expect", "beforeeach", "aftereach"
    ],
    "Version Control": [
        "git", "github", "gitlab", "bitbucket", "commit", "branch",
        "merge", "rebase", "pull request", "fork", "clone", "stash",
        "diff", "tag", "release", "workflow", "gitignore"
    ],
    "Security & Cybersecurity": [
        "encryption", "hashing", "vulnerability", "penetration testing",
        "firewall", "jwt", "oauth", "authentication", "authorization",
        "ssl", "tls", "xss", "csrf", "injection", "bcrypt",
        "salt", "sanitize", "rbac", "acl", "owasp", "cve",
        "password", "secret", "vault", "certificate"
    ],

    # --- Algorithms & Systems ---
    "Algorithms & Data Structures": [
        "algorithm", "complexity", "sorting", "searching", "binary search",
        "linked list", "stack", "queue", "heap", "hash table",
        "dynamic programming", "recursion", "traversal", "greedy",
        "backtracking", "memoization", "bfs", "dfs", "dijkstra",
        "quicksort", "mergesort", "trie", "segment tree", "big o"
    ],
    "System Programming": [
        "thread", "process", "mutex", "semaphore", "socket", "syscall",
        "buffer", "kernel", "filesystem", "ipc", "signal",
        "interrupt", "concurrent", "parallel", "deadlock", "race condition",
        "memory management", "garbage collection", "bitwise", "endian"
    ],

    # --- Game and Graphics ---
    "Game Development": [
        # Engines
        "unity", "unreal", "godot", "pygame", "phaser", "libgdx",
        "monogame", "raylib", "sdl", "sfml", "love2d", "cocos2d",
        "defold", "gdevelop", "construct",
        # Unity-specific
        "monobehaviour", "gameobject", "prefab", "transform", "rigidbody",
        "collider", "animator", "audiosource", "scriptableobject", "coroutine",
        "fixedupdate", "lateupdate", "instantiate", "awake", "onenable",
        "oncollisionenter", "ontriggerenter", "oncollisionexit", "ontriggerexit",
        "vector2", "vector3", "quaternion", "lerp", "slerp",
        # Unreal-specific
        "blueprint", "uobject", "uproperty", "ufunction", "acharacter",
        "apawn", "gamemode", "playercontroller", "tarray", "tmap",
        "uscene", "ustaticmesh", "skeletal", "blackboard", "behavior tree",
        # Godot-specific
        "gdscript", "node2d", "node3d", "characterbody", "kinematicbody",
        "area2d", "rigidbody2d", "animationplayer", "viewport", "autoload",
        # General game systems
        "shader", "sprite", "tilemap", "tileset", "scene", "animation",
        "physics", "collision detection", "navmesh", "pathfinding", "raycast",
        "particle", "hitbox", "hurtbox", "spawnpoint", "checkpoint",
        "inventory", "health", "respawn", "gameloop", "deltatime",
        "inputsystem", "keybinding", "gamepad", "controller", "joystick",
        "level design", "cutscene", "dialogue", "save system", "leaderboard",
        "multiplayer", "lobby", "matchmaking", "photon", "mirror", "netcode",
        # Audio
        "audioclip", "audiomixer", "sfx", "soundtrack",
        # 2D
        "platformer", "tilebased", "pixelart", "spritesheet", "parallax",
    ],
    "3D Rendering": [
        "webgl", "opengl", "three.js", "blender", "ray tracing", "lighting",
        "vertex", "fragment", "camera", "texture", "mesh", "shader",
        "vulkan", "directx", "metal", "glsl", "hlsl", "pbr",
        "normal map", "rasterization"
    ],
    "Computer Vision": [
        "opencv", "image processing", "object detection", "segmentation",
        "yolo", "resnet", "cnn", "convolution", "pooling", "feature map",
        "bounding box", "annotation", "augmentation", "torchvision",
        "pillow", "depth", "stereo", "tracking"
    ],

    # --- AI & NLP ---
    "AI & Natural Language Processing": [
        "nlp", "transformer", "bert", "gpt", "tokenization", "embedding",
        "language model", "gemini", "llm", "attention", "huggingface",
        "spacy", "nltk", "sentiment", "ner", "summarization",
        "translation", "generation", "fine tuning", "prompt", "rag",
        "vector store", "langchain", "openai", "anthropic", "llamaindex",
        "semantic search", "text classification"
    ],
}

# --- Subskills: only include libraries/technologies ---
SUBSKILL_KEYWORDS = {
    "Python": {
        "libraries": [
            "numpy", "pandas", "scipy", "matplotlib", "seaborn",
            "tensorflow", "keras", "pytorch", "sklearn", "xgboost",
            "transformers", "requests", "fastapi", "flask", "django",
            "sqlalchemy", "pydantic", "celery", "asyncio", "aiohttp",
            "pytest", "mypy", "poetry", "uvicorn", "httpx", "pillow",
            "boto3", "scrapy", "beautifulsoup", "paramiko"
        ],
        "language_features": [
            "async", "await", "decorator", "context manager",
            "generator", "comprehension", "dataclass", "typing"
        ]
    },
    "JavaScript": {
        "libraries": [
            "react", "vue", "angular", "express", "axios", "lodash",
            "jquery", "webpack", "vite", "babel", "eslint", "jest",
            "mocha", "nodemon", "socket.io", "nextjs", "nuxt"
        ],
        "tools": ["npm", "yarn", "pnpm", "vite", "webpack", "babel"]
    },
    "TypeScript": {
        "tools": ["tsc", "tsconfig"],
        "language_features": [
            "interface", "enum", "readonly", "generics",
            "decorator", "namespace", "infer", "keyof"
        ]
    },
    "Java": {
        "libraries": [
            "springframework", "spring", "hibernate", "junit",
            "mockito", "lombok", "jackson", "guava"
        ],
        "tools": ["maven", "gradle", "tomcat", "jetty"]
    },
    "Rust": {
        "libraries": ["tokio", "actix", "serde", "reqwest", "diesel"],
        "language_features": ["trait", "impl", "lifetime", "borrow", "ownership"]
    },
    "Go": {
        "libraries": ["gin", "fiber", "cobra", "viper", "gorm"],
        "tools": ["gomod", "gofmt", "gopath"]
    },
    "Machine Learning": {
        "libraries": [
            "tensorflow", "keras", "pytorch", "sklearn", "xgboost",
            "lightgbm", "catboost", "scikit"
        ],
        "algorithms": [
            "random forest", "gradient boosting", "neural network",
            "xgboost", "svm", "knn", "linear regression", "logistic regression",
            "decision tree", "naive bayes"
        ]
    },
    "Data Science": {
        "tools": ["pandas", "numpy", "matplotlib", "seaborn", "jupyter",
                  "statsmodels", "scipy", "plotly"]
    },
    "Web Development": {
        "libraries": [
            "react", "vue", "angular", "bootstrap", "tailwind",
            "nextjs", "nuxt", "svelte", "express", "fastapi"
        ],
        "tools": ["webpack", "vite", "babel", "npm", "yarn"]
    },
    "SQL": {
        "commands": [
            "select", "join", "create table", "insert into",
            "delete from", "update set", "where", "group by",
            "order by", "having", "union"
        ]
    },
    "Relational Databases": {
        "tools": ["mysql", "postgresql", "sqlite", "mariadb", "oracle"],
        "commands": ["select", "join", "where", "group by", "order by"]
    },
    "DevOps": {
        "tools": [
            "docker", "kubernetes", "jenkins", "terraform", "ansible",
            "helm", "prometheus", "grafana", "nginx", "argocd"
        ]
    },
    "Testing & QA": {
        "tools": [
            "pytest", "jest", "mocha", "cypress", "selenium",
            "playwright", "vitest", "unittest", "hypothesis"
        ]
    },
    "AI & Natural Language Processing": {
        "libraries": [
            "transformers", "spacy", "nltk", "langchain",
            "openai", "anthropic", "sentence transformers", "llamaindex"
        ],
        "tools": ["huggingface", "bert", "gpt", "llm", "rag"]
    },
    "Computer Vision": {
        "libraries": ["opencv", "pillow", "torchvision", "albumentations"],
        "algorithms": ["yolo", "resnet", "cnn", "object detection", "segmentation"]
    },
    "Cloud Computing": {
        "tools": ["aws", "azure", "gcp", "terraform", "serverless",
                  "lambda", "ec2", "s3", "rds", "fargate"]
    },
    "Game Development": {
        "engines": [
            "unity", "unreal", "godot", "pygame", "phaser", "libgdx",
            "monogame", "raylib", "sdl", "sfml", "love2d", "cocos2d"
        ],
        "libraries": [
            "monobehaviour", "rigidbody", "animator", "audiosource",
            "scriptableobject", "transform", "collider", "photon", "mirror"
        ],
        "tools": [
            "blueprint", "gdscript", "prefab", "navmesh", "tilemap",
            "behavior tree", "blackboard", "shader"
        ],
    },
}

# Maps file extensions to skills — used for reliable extension-based detection
# (a .py file is definitively Python regardless of keyword frequency)
EXT_SKILL_MAP = {
    ".py":    "Python",
    ".js":    "JavaScript",
    ".jsx":   "JavaScript",
    ".ts":    "TypeScript",
    ".tsx":   "TypeScript",
    ".java":  "Java",
    ".cpp":   "C/C++",
    ".cc":    "C/C++",
    ".cxx":   "C/C++",
    ".c":     "C/C++",
    ".cs":    "C#",
    ".rs":    "Rust",
    ".go":    "Go",
    ".rb":    "Ruby",
    ".php":   "PHP",
    ".swift": "Mobile Development",
    ".kt":    "Mobile Development",
    ".sql":   "SQL",
    ".gd":    "Game Development",   # Godot GDScript
    ".gdshader": "Game Development",  # Godot shaders
}
# Score added per file with a matching extension (counts toward raw_skill_hits too)
_EXT_BONUS_PER_FILE = 5

GENERIC_SKILLS = {
    "Backend Development", "Frontend Development",
    "API Development", "Database Management", "DevOps"
}

ADVANCED_KEYWORDS = [
    "async", "await", "decorator", "pipeline", "architecture", "microservice", "orm"
]

CORE_FOLDERS = ["src", "app", "main"]
PERIPHERAL_FOLDERS = ["tests", "docs", "scripts"]

VALID_SUBSKILL_GROUPS = {"libraries", "tools", "multi_word", "algorithms", "language_features", "commands"}

# --- Precomputed lookup structures (built once at import time) ---
# Keywords that are purely alphanumeric (e.g. "python", "neo4j") can be matched
# via a single Counter tokenization pass instead of per-keyword regex.
# Everything else (spaces, dots, slashes like "react native", "three.js", "ci/cd")
# falls back to a pre-compiled regex pattern.
_SIMPLE_KW_RE = re.compile(r'^[a-z][a-z0-9]*$')
_TOKENIZE_RE = re.compile(r'\b[a-z][a-z0-9]*\b')
_ADVANCED_KEYWORDS_SET = frozenset(kw.lower() for kw in ADVANCED_KEYWORDS)
# Max file size to read (skip huge minified/generated files)
_MAX_FILE_BYTES = 512 * 1024  # 512 KB


def _build_skill_lookups(keyword_dict):
    """Split each skill's keywords into a fast single-word set and precompiled patterns."""
    result = {}
    for key, keywords in keyword_dict.items():
        singles = set()
        multis = []
        for kw in keywords:
            kw_l = kw.lower()
            if _SIMPLE_KW_RE.match(kw_l):
                singles.add(kw_l)
            else:
                multis.append((kw_l, re.compile(r'\b' + re.escape(kw_l) + r'\b')))
        result[key] = (singles, multis)
    return result


def _build_subskill_lookups(subskill_dict):
    result = {}
    for skill, groups in subskill_dict.items():
        result[skill] = {}
        for group, keywords in groups.items():
            singles = set()
            multis = []
            for kw in keywords:
                kw_l = kw.lower()
                if _SIMPLE_KW_RE.match(kw_l):
                    singles.add(kw_l)
                else:
                    multis.append((kw_l, re.compile(r'\b' + re.escape(kw_l) + r'\b')))
            result[skill][group] = (singles, multis)
    return result


_SKILL_LOOKUPS = _build_skill_lookups(SKILL_KEYWORDS)
_SUBSKILL_LOOKUPS = _build_subskill_lookups(SUBSKILL_KEYWORDS)

# --- Skill analyzer function ---
def analyze_coding_skills_refined(folder_path, file_extensions=None):
    folder = Path(folder_path)
    if not folder.is_dir():
        raise NotADirectoryError(f"{folder_path} is not a valid folder")

    skill_scores = defaultdict(float)
    skill_subskills = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    project_detected_skills = set()
    raw_skill_hits = defaultdict(int)

    for file in folder.rglob("*"):
        if not file.is_file():
            continue
        if file_extensions and file.suffix not in file_extensions:
            continue
        try:
            if file.stat().st_size > _MAX_FILE_BYTES:
                continue
        except OSError:
            continue

        try:
            text = file.read_text(encoding="utf-8").lower()
        except (UnicodeDecodeError, OSError):
            continue

        parts = [p.lower() for p in file.parts]
        if any(cf in parts for cf in CORE_FOLDERS):
            folder_weight = 1.5
        elif any(pf in parts for pf in PERIPHERAL_FOLDERS):
            folder_weight = 0.8
        else:
            folder_weight = 1.0

        # Tokenize once — single-word keywords are looked up in O(1) via Counter
        word_counter = Counter(_TOKENIZE_RE.findall(text))

        detected_skills = set()

        # --- 0: Extension-based detection (strong authoritative signal) ---
        ext_skill = EXT_SKILL_MAP.get(file.suffix.lower())
        if ext_skill:
            raw_skill_hits[ext_skill] += _EXT_BONUS_PER_FILE
            skill_scores[ext_skill] += _EXT_BONUS_PER_FILE * folder_weight
            detected_skills.add(ext_skill)

        # --- 1: Top-level skills ---
        for skill, (singles, multis) in _SKILL_LOOKUPS.items():
            count = 0
            for kw in singles:
                count += word_counter.get(kw, 0)
            for kw, pattern in multis:
                count += len(pattern.findall(text))
            if count:
                detected_skills.add(skill)
                raw_skill_hits[skill] += count
                skill_scores[skill] += count * folder_weight

        # --- 2: Subskills (only if parent skill detected) ---
        for skill, groups in _SUBSKILL_LOOKUPS.items():
            if skill not in detected_skills:
                continue
            for group, (singles, multis) in groups.items():
                for kw in singles:
                    count = word_counter.get(kw, 0)
                    if count:
                        raw_skill_hits[skill] += count
                        skill_subskills[skill][group][kw] += count
                        boost = 0.5 if kw in _ADVANCED_KEYWORDS_SET else 0.3
                        skill_scores[skill] += count * boost * folder_weight
                for kw, pattern in multis:
                    count = len(pattern.findall(text))
                    if count:
                        raw_skill_hits[skill] += count
                        skill_subskills[skill][group][kw] += count
                        boost = 0.5 if kw in _ADVANCED_KEYWORDS_SET else 0.3
                        skill_scores[skill] += count * boost * folder_weight

        project_detected_skills.update(detected_skills)

    # --- Nothing detected ---
    if not skill_scores:
        return {"skills": {}, "skill_combinations": {}}

    # --- 3️⃣ Filter weak skills ---
    MIN_RAW_COUNT = 3
    filtered_scores = {skill: score for skill, score in skill_scores.items() if raw_skill_hits[skill] >= MIN_RAW_COUNT}
    if not filtered_scores:
        return {"skills": {}, "skill_combinations": {}}

    # --- 4️⃣ Normalize scores ---
    total_score = sum(filtered_scores.values())
    normalized_scores = {skill: round(score / total_score, 3) for skill, score in filtered_scores.items()}

    # --- 5️⃣ Skill combinations ---
    combinations = defaultdict(float)
    skills = sorted(filtered_scores.keys())
    for i in range(len(skills)):
        for j in range(i + 1, len(skills)):
            combinations[(skills[i], skills[j])] += 1
    max_comb = max(combinations.values(), default=1)
    normalized_combinations = {pair: round(val / max_comb, 3) for pair, val in combinations.items()}

    # --- 6️⃣ Final output ---
    final_output = {}
    for skill, score in normalized_scores.items():
        if skill in GENERIC_SKILLS:
            continue
        final_output[skill] = {
            "score": score,
            "subskills": {
                group: dict(sorted(items.items(), key=lambda x: x[1], reverse=True))
                for group, items in skill_subskills[skill].items()
                if items and group in VALID_SUBSKILL_GROUPS
            }
        }

    return {
        "skills": dict(sorted(final_output.items(), key=lambda x: x[1]["score"], reverse=True)),
        "skill_combinations": dict(sorted(normalized_combinations.items(), key=lambda x: x[1], reverse=True))
    }
