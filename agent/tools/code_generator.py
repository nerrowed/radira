"""Code generator tool for general programming languages using LLM."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import logging

from .base import BaseTool, ToolResult, ToolStatus
from agent.llm.groq_client import get_groq_client
from agent.llm.prompts import CODE_GENERATOR_SYSTEM_PROMPT
from agent.llm.parsers import CodeParser
from config.settings import settings

logger = logging.getLogger(__name__)


class CodeGeneratorTool(BaseTool):
    """Tool for generating code in various programming languages using LLM."""

    LANGUAGES = {
        'c': {'name': 'C Programming Language', 'ext': '.c', 'parser': 'c'},
        'cpp': {'name': 'C++', 'ext': '.cpp', 'parser': 'cpp'},
        'python': {'name': 'Python', 'ext': '.py', 'parser': 'python'},
        'java': {'name': 'Java', 'ext': '.java', 'parser': 'java'},
        'rust': {'name': 'Rust', 'ext': '.rs', 'parser': 'rust'},
        'go': {'name': 'Go', 'ext': '.go', 'parser': 'go'},
        'javascript': {'name': 'JavaScript', 'ext': '.js', 'parser': 'javascript'},
        'typescript': {'name': 'TypeScript', 'ext': '.ts', 'parser': 'typescript'},
        'csharp': {'name': 'C#', 'ext': '.cs', 'parser': 'csharp'},
        'ruby': {'name': 'Ruby', 'ext': '.rb', 'parser': 'ruby'},
        'php': {'name': 'PHP', 'ext': '.php', 'parser': 'php'},
        'swift': {'name': 'Swift', 'ext': '.swift', 'parser': 'swift'},
        'kotlin': {'name': 'Kotlin', 'ext': '.kt', 'parser': 'kotlin'},
    }

    def __init__(self, output_directory: Optional[str] = None):
        """Initialize code generator tool.

        Args:
            output_directory: Directory for generated files
        """
        super().__init__()
        self.output_dir = Path(output_directory or settings.working_directory) / "generated_code"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm = get_groq_client()

    @property
    def name(self) -> str:
        return "code_generator"

    @property
    def description(self) -> str:
        return "Generate code in various programming languages (C, C++, Python, Java, Rust, Go, etc.) from natural language descriptions"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "description": {
                "type": "string",
                "description": "Description of the code/program to generate",
                "required": True
            },
            "language": {
                "type": "string",
                "description": f"Programming language to use: {', '.join(self.LANGUAGES.keys())}",
                "required": True
            },
            "filename": {
                "type": "string",
                "description": "Output filename (without extension)",
                "required": False
            },
            "features": {
                "type": "array",
                "description": "List of specific features or requirements to include",
                "required": False
            },
            "include_tests": {
                "type": "boolean",
                "description": "Whether to include test code",
                "required": False
            },
            "include_docs": {
                "type": "boolean",
                "description": "Whether to include documentation/comments",
                "required": False
            }
        }

    @property
    def category(self) -> str:
        return "code_generation"

    @property
    def examples(self) -> List[str]:
        return [
            "Python script: {'description': 'Binary search algorithm', 'language': 'python'}",
            "C program: {'description': 'Linked list implementation', 'language': 'c', 'filename': 'linked_list'}",
            "Rust app: {'description': 'File compression utility', 'language': 'rust', 'include_tests': True}"
        ]

    def execute(self, **kwargs) -> ToolResult:
        """Generate code in specified language.

        Args:
            description: Code description
            language: Programming language
            filename: Output filename
            features: Additional features
            include_tests: Include test code
            include_docs: Include documentation

        Returns:
            ToolResult with generated files info
        """
        description = kwargs.get("description", "")
        language = kwargs.get("language", "").lower()
        filename = kwargs.get("filename", "main")
        features = kwargs.get("features", [])
        include_tests = kwargs.get("include_tests", False)
        include_docs = kwargs.get("include_docs", True)

        if not description:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error="No description provided"
            )

        if not language:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error="No language specified"
            )

        if language not in self.LANGUAGES:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Unknown language '{language}'. Available: {', '.join(self.LANGUAGES.keys())}"
            )

        try:
            # Generate based on language
            result = self._generate_code(
                description,
                language,
                filename,
                features,
                include_tests,
                include_docs
            )
            return result

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Generation failed: {str(e)}"
            )

    def _generate_code(
        self,
        description: str,
        language: str,
        filename: str,
        features: List[str],
        include_tests: bool,
        include_docs: bool
    ) -> ToolResult:
        """Generate code for specified language."""
        lang_info = self.LANGUAGES[language]
        features_text = ", ".join(features) if features else "basic functionality"

        # Build language-specific requirements
        requirements = self._get_language_requirements(language, include_tests, include_docs)

        prompt = f"""Generate a complete, production-ready {lang_info['name']} program with the following requirements:

Description: {description}
Features: {features_text}

Requirements:
{requirements}

Generate complete, ready-to-use code. Output only the code, no explanations unless absolutely necessary.
"""

        # Get LLM response
        messages = [
            {"role": "system", "content": CODE_GENERATOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = self.llm.chat(messages=messages, temperature=0.5, max_tokens=8000)
        code = response["content"]

        # Extract code from markdown if present
        extracted_code = CodeParser.extract_single_code_block(code, lang_info['parser'])
        if extracted_code:
            code = extracted_code

        # Save main code file
        output_path = self.output_dir / f"{filename}{lang_info['ext']}"
        output_path.write_text(code, encoding='utf-8')

        generated_files = [str(output_path)]

        # Generate additional files based on language
        additional_files = self._generate_additional_files(language, filename, description)
        generated_files.extend(additional_files)

        return ToolResult(
            status=ToolStatus.SUCCESS,
            output=f"Generated {lang_info['name']} code: {output_path}",
            metadata={
                "path": str(output_path),
                "language": language,
                "size": len(code),
                "files": generated_files
            }
        )

    def _get_language_requirements(self, language: str, include_tests: bool, include_docs: bool) -> str:
        """Get language-specific requirements."""
        base_requirements = {
            'c': """- Use modern C (C11 or later) standards
- Include proper header guards
- Use meaningful variable names
- Implement proper error handling
- Include memory management (malloc/free if needed)
- Add function prototypes
- Use const where appropriate""",

            'cpp': """- Use modern C++ (C++17 or later) standards
- Use RAII principles
- Prefer STL containers over raw arrays
- Use smart pointers (unique_ptr, shared_ptr)
- Implement proper constructors/destructors
- Use const correctness
- Add namespace if appropriate""",

            'python': """- Follow PEP 8 style guide
- Use type hints (Python 3.6+)
- Include docstrings for functions/classes
- Use list comprehensions where appropriate
- Implement proper exception handling
- Use context managers for resources
- Make it Python 3.x compatible""",

            'java': """- Follow Java naming conventions
- Use proper access modifiers
- Implement interfaces where appropriate
- Use generics for type safety
- Include proper exception handling
- Follow SOLID principles
- Use modern Java features (Java 11+)""",

            'rust': """- Follow Rust naming conventions
- Use ownership and borrowing correctly
- Implement proper error handling (Result, Option)
- Use iterators and closures appropriately
- Include proper lifetime annotations if needed
- Use cargo-compatible structure
- Follow Rust best practices""",

            'go': """- Follow Go naming conventions
- Use proper error handling (error return values)
- Implement interfaces where appropriate
- Use goroutines and channels if concurrent
- Include proper package documentation
- Follow Go best practices
- Use modern Go features (Go 1.18+)""",

            'javascript': """- Use modern ES6+ syntax
- Use const/let instead of var
- Implement proper error handling
- Use async/await for asynchronous code
- Follow JavaScript best practices
- Include JSDoc comments if needed""",

            'typescript': """- Use proper TypeScript types
- Avoid 'any' type where possible
- Use interfaces and type aliases
- Implement generics where appropriate
- Use strict mode
- Follow TypeScript best practices""",

            'csharp': """- Follow C# naming conventions
- Use LINQ where appropriate
- Implement proper exception handling
- Use async/await for asynchronous code
- Follow SOLID principles
- Use modern C# features (C# 9+)""",

            'ruby': """- Follow Ruby style guide
- Use idiomatic Ruby patterns
- Implement proper blocks and iterators
- Use symbols and hashes appropriately
- Include proper error handling
- Follow Ruby best practices""",

            'php': """- Use modern PHP (PHP 8+)
- Follow PSR standards
- Use type declarations
- Implement proper error handling
- Use namespaces appropriately
- Follow PHP best practices""",

            'swift': """- Follow Swift naming conventions
- Use optionals properly
- Implement protocol-oriented programming
- Use guard statements for early returns
- Follow Swift best practices
- Use modern Swift features (Swift 5+)""",

            'kotlin': """- Follow Kotlin conventions
- Use null safety features
- Implement extension functions where appropriate
- Use data classes for data structures
- Follow Kotlin best practices
- Use modern Kotlin features"""
        }

        requirements = base_requirements.get(language, "- Follow best practices for the language")

        if include_docs:
            requirements += "\n- Include comprehensive comments and documentation"

        if include_tests:
            requirements += "\n- Include basic unit tests or test cases"

        return requirements

    def _generate_additional_files(self, language: str, filename: str, description: str) -> List[str]:
        """Generate additional files based on language (build files, configs, etc.)."""
        additional_files = []

        try:
            if language == 'c':
                # Generate Makefile
                makefile_content = f"""# Makefile for {filename}
CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O2
TARGET = {filename}
SRC = {filename}.c

all: $(TARGET)

$(TARGET): $(SRC)
\t$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

clean:
\trm -f $(TARGET)

run: $(TARGET)
\t./$(TARGET)

.PHONY: all clean run
"""
                makefile_path = self.output_dir / "Makefile"
                makefile_path.write_text(makefile_content, encoding='utf-8')
                additional_files.append(str(makefile_path))

            elif language == 'cpp':
                # Generate CMakeLists.txt
                cmake_content = f"""cmake_minimum_required(VERSION 3.10)
project({filename})

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable({filename} {filename}.cpp)

# Compiler warnings
if(MSVC)
    target_compile_options({filename} PRIVATE /W4)
else()
    target_compile_options({filename} PRIVATE -Wall -Wextra -pedantic)
endif()
"""
                cmake_path = self.output_dir / "CMakeLists.txt"
                cmake_path.write_text(cmake_content, encoding='utf-8')
                additional_files.append(str(cmake_path))

            elif language == 'python':
                # Generate requirements.txt
                requirements_content = "# Python dependencies\n# Add your dependencies here\n"
                req_path = self.output_dir / "requirements.txt"
                req_path.write_text(requirements_content, encoding='utf-8')
                additional_files.append(str(req_path))

            elif language == 'rust':
                # Generate Cargo.toml
                cargo_content = f"""[package]
name = "{filename}"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
                cargo_path = self.output_dir / "Cargo.toml"
                cargo_path.write_text(cargo_content, encoding='utf-8')
                additional_files.append(str(cargo_path))

            elif language == 'go':
                # Generate go.mod
                gomod_content = f"""module {filename}

go 1.21
"""
                gomod_path = self.output_dir / "go.mod"
                gomod_path.write_text(gomod_content, encoding='utf-8')
                additional_files.append(str(gomod_path))

            elif language in ['javascript', 'typescript']:
                # Generate package.json
                package_json = {
                    "name": filename,
                    "version": "1.0.0",
                    "description": description,
                    "main": f"{filename}.{self.LANGUAGES[language]['ext'][1:]}",
                    "scripts": {
                        "start": f"node {filename}.js"
                    }
                }
                if language == 'typescript':
                    package_json["scripts"] = {
                        "build": "tsc",
                        "start": f"node {filename}.js"
                    }
                    package_json["devDependencies"] = {
                        "typescript": "^5.0.0"
                    }

                package_path = self.output_dir / "package.json"
                package_path.write_text(json.dumps(package_json, indent=2), encoding='utf-8')
                additional_files.append(str(package_path))

        except Exception as e:
            logger.warning(f"Failed to generate additional files: {e}")

        return additional_files

    @property
    def is_dangerous(self) -> bool:
        return False
