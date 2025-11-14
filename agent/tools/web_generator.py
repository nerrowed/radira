"""Web application generator tool using LLM."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import logging

from .base import BaseTool, ToolResult, ToolStatus
from agent.llm.groq_client import get_groq_client
from agent.llm.prompts import WEB_GENERATOR_SYSTEM_PROMPT
from agent.llm.parsers import CodeParser
from config.settings import settings

logger = logging.getLogger(__name__)


class WebGeneratorTool(BaseTool):
    """Tool for generating web applications using LLM."""

    FRAMEWORKS = {
        'html': 'Plain HTML/CSS/JavaScript',
        'react': 'React with JSX',
        'vue': 'Vue.js',
        'tailwind': 'HTML with Tailwind CSS'
    }

    def __init__(self, output_directory: Optional[str] = None):
        """Initialize web generator tool.

        Args:
            output_directory: Directory for generated files
        """
        super().__init__()
        self.output_dir = Path(output_directory or settings.working_directory) / "generated_web"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm = get_groq_client()

    @property
    def name(self) -> str:
        return "web_generator"

    @property
    def description(self) -> str:
        return "Generate complete web applications (HTML, CSS, JavaScript) from natural language descriptions"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "description": {
                "type": "string",
                "description": "Description of the web app to generate",
                "required": True
            },
            "framework": {
                "type": "string",
                "description": f"Framework to use: {', '.join(self.FRAMEWORKS.keys())}",
                "required": False
            },
            "filename": {
                "type": "string",
                "description": "Output filename (without extension)",
                "required": False
            },
            "features": {
                "type": "array",
                "description": "List of specific features to include",
                "required": False
            }
        }

    @property
    def category(self) -> str:
        return "web_generation"

    @property
    def examples(self) -> List[str]:
        return [
            "Simple page: {'description': 'A landing page for a coffee shop', 'framework': 'html'}",
            "React app: {'description': 'Todo list app', 'framework': 'react'}",
            "Styled page: {'description': 'Portfolio website', 'framework': 'tailwind', 'features': ['responsive', 'dark mode']}"
        ]

    def execute(self, **kwargs) -> ToolResult:
        """Generate web application.

        Args:
            description: App description
            framework: Framework to use
            filename: Output filename
            features: Additional features

        Returns:
            ToolResult with generated files info
        """
        description = kwargs.get("description", "")
        framework = kwargs.get("framework", "html").lower()
        filename = kwargs.get("filename", "index")
        features = kwargs.get("features", [])

        if not description:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error="No description provided"
            )

        if framework not in self.FRAMEWORKS:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Unknown framework '{framework}'. Available: {', '.join(self.FRAMEWORKS.keys())}"
            )

        try:
            # Generate based on framework
            if framework == 'html':
                result = self._generate_html(description, filename, features)
            elif framework == 'react':
                result = self._generate_react(description, filename, features)
            elif framework == 'vue':
                result = self._generate_vue(description, filename, features)
            elif framework == 'tailwind':
                result = self._generate_tailwind(description, filename, features)
            else:
                result = self._generate_html(description, filename, features)

            return result

        except Exception as e:
            logger.error(f"Web generation failed: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Generation failed: {str(e)}"
            )

    def _generate_html(self, description: str, filename: str, features: List[str]) -> ToolResult:
        """Generate plain HTML/CSS/JS application."""
        # Create prompt
        features_text = ", ".join(features) if features else "basic functionality"
        prompt = f"""Generate a complete, modern HTML web page with the following requirements:

Description: {description}
Features: {features_text}

Requirements:
- Use modern HTML5 semantic elements
- Include embedded CSS in <style> tag (make it beautiful and modern)
- Include JavaScript in <script> tag if needed
- Make it responsive (mobile-friendly)
- Use modern design principles
- Include comments explaining key parts

Generate complete, ready-to-use HTML file. Output only the code, no explanations.
"""

        # Get LLM response
        messages = [
            {"role": "system", "content": WEB_GENERATOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = self.llm.chat(messages=messages, temperature=0.7, max_tokens=8000)
        code = response["content"]

        # Extract code from markdown if present
        extracted_code = CodeParser.extract_single_code_block(code, 'html')
        if extracted_code:
            code = extracted_code

        # Save file
        output_path = self.output_dir / f"{filename}.html"
        output_path.write_text(code, encoding='utf-8')

        return ToolResult(
            status=ToolStatus.SUCCESS,
            output=f"Generated HTML file: {output_path}",
            metadata={
                "path": str(output_path),
                "framework": "html",
                "size": len(code)
            }
        )

    def _generate_react(self, description: str, filename: str, features: List[str]) -> ToolResult:
        """Generate React application."""
        features_text = ", ".join(features) if features else "basic functionality"
        prompt = f"""Generate a complete React component with the following requirements:

Description: {description}
Features: {features_text}

Requirements:
- Use React functional components with hooks
- Include all necessary imports
- Use modern JavaScript (ES6+)
- Add inline styles or CSS-in-JS
- Make it responsive
- Include comments

Generate complete, ready-to-use React code. Output only the code, no explanations.
"""

        messages = [
            {"role": "system", "content": WEB_GENERATOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = self.llm.chat(messages=messages, temperature=0.7, max_tokens=8000)
        code = response["content"]

        # Extract code
        extracted_code = CodeParser.extract_single_code_block(code, 'jsx')
        if not extracted_code:
            extracted_code = CodeParser.extract_single_code_block(code, 'javascript')
        if extracted_code:
            code = extracted_code

        # Save files
        output_path = self.output_dir / f"{filename}.jsx"
        output_path.write_text(code, encoding='utf-8')

        # Also generate package.json
        package_json = {
            "name": filename,
            "version": "1.0.0",
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0"
            }
        }
        package_path = self.output_dir / "package.json"
        package_path.write_text(json.dumps(package_json, indent=2), encoding='utf-8')

        return ToolResult(
            status=ToolStatus.SUCCESS,
            output=f"Generated React app: {output_path} and package.json",
            metadata={
                "path": str(output_path),
                "framework": "react",
                "files": [str(output_path), str(package_path)]
            }
        )

    def _generate_vue(self, description: str, filename: str, features: List[str]) -> ToolResult:
        """Generate Vue.js application."""
        features_text = ", ".join(features) if features else "basic functionality"
        prompt = f"""Generate a complete Vue.js component with the following requirements:

Description: {description}
Features: {features_text}

Requirements:
- Use Vue 3 Composition API
- Include template, script, and style sections
- Use modern JavaScript
- Make it responsive
- Include comments

Generate complete Vue component file. Output only the code, no explanations.
"""

        messages = [
            {"role": "system", "content": WEB_GENERATOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = self.llm.chat(messages=messages, temperature=0.7, max_tokens=8000)
        code = response["content"]

        # Extract code
        extracted_code = CodeParser.extract_single_code_block(code, 'vue')
        if extracted_code:
            code = extracted_code

        # Save file
        output_path = self.output_dir / f"{filename}.vue"
        output_path.write_text(code, encoding='utf-8')

        return ToolResult(
            status=ToolStatus.SUCCESS,
            output=f"Generated Vue component: {output_path}",
            metadata={
                "path": str(output_path),
                "framework": "vue",
                "size": len(code)
            }
        )

    def _generate_tailwind(self, description: str, filename: str, features: List[str]) -> ToolResult:
        """Generate HTML with Tailwind CSS."""
        features_text = ", ".join(features) if features else "basic functionality"
        prompt = f"""Generate a complete HTML web page using Tailwind CSS with the following requirements:

Description: {description}
Features: {features_text}

Requirements:
- Use Tailwind CSS via CDN
- Use modern HTML5 semantic elements
- Make it fully responsive with Tailwind classes
- Include JavaScript if needed
- Use Tailwind's design system (colors, spacing, etc.)
- Make it beautiful and modern
- Include comments

Generate complete HTML file with Tailwind. Output only the code, no explanations.
"""

        messages = [
            {"role": "system", "content": WEB_GENERATOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = self.llm.chat(messages=messages, temperature=0.7, max_tokens=8000)
        code = response["content"]

        # Extract code
        extracted_code = CodeParser.extract_single_code_block(code, 'html')
        if extracted_code:
            code = extracted_code

        # Save file
        output_path = self.output_dir / f"{filename}.html"
        output_path.write_text(code, encoding='utf-8')

        return ToolResult(
            status=ToolStatus.SUCCESS,
            output=f"Generated Tailwind page: {output_path}",
            metadata={
                "path": str(output_path),
                "framework": "tailwind",
                "size": len(code)
            }
        )

    @property
    def is_dangerous(self) -> bool:
        return False
