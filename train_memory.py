#!/usr/bin/env python3
"""Training script untuk menambahkan memori tentang tools, scripts, dan workflow.

Script ini menambahkan pengetahuan dasar ke memory system tentang:
- Cara penggunaan tools
- Lokasi script dan file output
- Cara membaca output
- Best practices untuk berbagai operasi
"""

import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Try to import yaml, fallback if not available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce ChromaDB verbose logging
logging.getLogger("chromadb.api.segment").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.learning.learning_manager import get_learning_manager
from agent.state.memory_manager import get_memory_manager
from config.settings import settings


class MemoryTrainer:
    """Trainer untuk menambahkan pengetahuan ke memory system."""
    
    def __init__(self):
        self.learning_manager = get_learning_manager()
        self.memory_manager = get_memory_manager()
        self.workspace_dir = Path(settings.working_directory)
        
    def train_all(self):
        """Jalankan semua training modules."""
        logger.info("🚀 Starting memory training...")
        
        try:
            # 1. Tool usage patterns
            self.train_tool_usage()
            
            # 2. File system operations
            self.train_file_operations()
            
            # 3. Terminal commands
            self.train_terminal_operations()
            
            # 4. Output locations
            self.train_output_locations()
            
            # 5. Reading outputs
            self.train_reading_outputs()
            
            # 6. Pentest workflows
            self.train_pentest_workflows()
            
            # 7. Best practices
            self.train_best_practices()
            
            logger.info("✅ Memory training completed successfully!")
            
            # Show statistics - get directly from memory to ensure fresh count
            if self.memory_manager.vector_memory.available:
                exp_count = self.memory_manager.vector_memory.experiences.count()
                lesson_count = self.memory_manager.vector_memory.lessons.count()
                strategy_count = self.memory_manager.vector_memory.strategies.count()
                
                logger.info(f"\n📊 Training Summary:")
                logger.info(f"   Experiences: {exp_count}")
                logger.info(f"   Lessons: {lesson_count}")
                logger.info(f"   Strategies: {strategy_count}")
                logger.info(f"   Backend: chromadb")
                logger.info(f"   Storage: {self.memory_manager.vector_memory.persist_directory}")
            else:
                stats = self.learning_manager.get_learning_statistics()
                logger.info(f"\n📊 Training Summary:")
                logger.info(f"   Experiences: {stats.get('total_experiences', 0)}")
                logger.info(f"   Lessons: {stats.get('total_lessons', 0)}")
                logger.info(f"   Strategies: {stats.get('total_strategies', 0)}")
                logger.info(f"   Backend: {stats.get('backend', 'unknown')}")
                logger.info(f"   Storage: {stats.get('storage_path', 'N/A')}")
            
        except Exception as e:
            logger.error(f"❌ Training failed: {e}", exc_info=True)
            raise
    
    def train_tool_usage(self):
        """Train tentang cara penggunaan tools."""
        logger.info("📚 Training: Tool Usage Patterns")
        
        # File System Tool
        self.learning_manager.learn_from_task(
            task="Membaca file output pentest",
            actions=[
                "file_system.list untuk melihat direktori pentest_output",
                "file_system.read untuk membaca file .txt di pentest_output"
            ],
            outcome="Berhasil membaca file output pentest dari workspace/pentest_output/",
            success=True,
            context={
                "tool": "file_system",
                "operation": "read",
                "output_location": "workspace/pentest_output/"
            }
        )
        
        self.memory_manager.add_lesson(
            lesson="File system tool menggunakan path relatif dari workspace. Gunakan 'pentest_output/' bukan '/home/.../pentest_output'",
            context="File operations",
            category="tool_usage",
            importance=0.9
        )
        
        self.memory_manager.add_strategy(
            strategy="List directory dulu sebelum read file untuk memastikan file exists",
            task_type="file_operations",
            success_rate=0.95,
            context="Reading files from output directories"
        )
        
        # Terminal Tool
        self.learning_manager.learn_from_task(
            task="Filter subdomain dengan httpx",
            actions=[
                "terminal.execute dengan command httpx untuk filter URL aktif"
            ],
            outcome="Berhasil filter subdomain aktif menggunakan httpx",
            success=True,
            context={
                "tool": "terminal",
                "command": "httpx",
                "use_case": "filter_active_urls"
            }
        )
        
        self.memory_manager.add_lesson(
            lesson="httpx command: 'httpx -l <file> -o <output>' untuk filter URL aktif dari list. Gunakan check_output=true untuk capture hasil",
            context="Terminal operations",
            category="tool_usage",
            importance=0.9
        )
        
        # Pentest Tool
        self.learning_manager.learn_from_task(
            task="Subdomain enumeration dengan subfinder",
            actions=[
                "pentest.subdomain_enumeration dengan domain dan tool subfinder",
                "Output disimpan ke pentest_output/",
                "file_system.read untuk membaca hasil"
            ],
            outcome="Berhasil enumerate subdomain dan menyimpan ke pentest_output/subdomains.txt",
            success=True,
            context={
                "tool": "pentest",
                "operation": "subdomain_enumeration",
                "output_format": "txt",
                "output_location": "pentest_output/"
            }
        )
        
        self.memory_manager.add_lesson(
            lesson="Pentest tool menyimpan output ke workspace/pentest_output/ dengan format .txt. File biasanya bernama subdomains.txt, scan_results.txt, dll",
            context="Pentest tool output",
            category="tool_usage",
            importance=0.9
        )
        
        self.memory_manager.add_strategy(
            strategy="Subdomain enumeration → Save to pentest_output → Read file → Filter with httpx",
            task_type="security_testing",
            success_rate=0.9,
            context="Complete subdomain enumeration workflow"
        )
    
    def train_file_operations(self):
        """Train tentang file operations."""
        logger.info("📚 Training: File Operations")
        
        lessons = [
            {
                "lesson": "Path untuk file_system tool adalah relatif dari workspace. Contoh: 'pentest_output/subdomains.txt' bukan absolute path",
                "context": "File path resolution",
                "category": "file_operations",
                "importance": 0.95
            },
            {
                "lesson": "Selalu list directory dulu sebelum read untuk memastikan file exists dan melihat struktur direktori",
                "context": "File reading workflow",
                "category": "file_operations",
                "importance": 0.9
            },
            {
                "lesson": "File output pentest biasanya di workspace/pentest_output/ dengan format .txt",
                "context": "Output file locations",
                "category": "file_operations",
                "importance": 0.85
            },
            {
                "lesson": "Gunakan file_system.search dengan pattern '*.txt' untuk mencari semua file output di direktori",
                "context": "Finding output files",
                "category": "file_operations",
                "importance": 0.8
            }
        ]
        
        for lesson_data in lessons:
            self.memory_manager.add_lesson(**lesson_data)
        
        # Experience: Reading pentest output
        self.learning_manager.learn_from_task(
            task="Membaca semua file output pentest",
            actions=[
                "file_system.list path='pentest_output'",
                "file_system.search path='pentest_output' pattern='*.txt'",
                "file_system.read untuk setiap file yang ditemukan"
            ],
            outcome="Berhasil membaca semua file output dari pentest_output/",
            success=True,
            context={
                "output_directory": "workspace/pentest_output/",
                "file_pattern": "*.txt"
            }
        )
    
    def train_terminal_operations(self):
        """Train tentang terminal operations."""
        logger.info("📚 Training: Terminal Operations")
        
        lessons = [
            {
                "lesson": "httpx command untuk filter URL aktif: 'httpx -l <input_file> -o <output_file> -status-code -title'. Gunakan -l untuk list input, -o untuk output",
                "context": "httpx usage",
                "category": "terminal_operations",
                "importance": 0.9
            },
            {
                "lesson": "Selalu set check_output=true saat menggunakan terminal tool untuk capture command output",
                "context": "Terminal tool parameters",
                "category": "tool_usage",
                "importance": 0.95
            },
            {
                "lesson": "Command httpx bisa membaca dari stdin atau file. Format: 'httpx -l <file>' atau 'cat <file> | httpx'",
                "context": "httpx input methods",
                "category": "terminal_operations",
                "importance": 0.85
            },
            {
                "lesson": "Untuk filter subdomain aktif, gunakan: 'httpx -l subdomains.txt -o active.txt -status-code -title -follow-redirects'",
                "context": "Filtering active URLs",
                "category": "terminal_operations",
                "importance": 0.9
            }
        ]
        
        for lesson_data in lessons:
            self.memory_manager.add_lesson(**lesson_data)
        
        # Strategy: Complete filtering workflow
        self.memory_manager.add_strategy(
            strategy="Read subdomain file → Pipe to httpx → Save active URLs → Read results",
            task_type="security_testing",
            success_rate=0.9,
            context="Filtering active subdomains with httpx"
        )
    
    def train_output_locations(self):
        """Train tentang lokasi file output."""
        logger.info("📚 Training: Output Locations")
        
        output_locations = {
            "pentest_output": {
                "path": "workspace/pentest_output/",
                "description": "Directory untuk semua output pentest (subdomain, scan results, dll)",
                "file_types": [".txt", ".json"],
                "common_files": ["subdomains.txt", "active_urls.txt", "scan_results.txt"]
            },
            "generated_web": {
                "path": "workspace/generated_web/",
                "description": "Directory untuk generated web files",
                "file_types": [".html", ".css", ".js"]
            },
            "generated_code": {
                "path": "workspace/generated_code/",
                "description": "Directory untuk generated code files",
                "file_types": [".py", ".js", ".html"]
            }
        }
        
        for location_name, location_info in output_locations.items():
            lesson = (
                f"Output directory {location_name} berada di {location_info['path']}. "
                f"File biasanya berformat {', '.join(location_info['file_types'])}. "
                f"Contoh file: {', '.join(location_info.get('common_files', []))}"
            )
            
            self.memory_manager.add_lesson(
                lesson=lesson,
                context="Output file locations",
                category="file_locations",
                importance=0.9
            )
        
        # Experience: Finding output files
        self.learning_manager.learn_from_task(
            task="Mencari file output pentest",
            actions=[
                "file_system.list path='pentest_output'",
                "file_system.search path='pentest_output' pattern='*.txt'"
            ],
            outcome=f"File output ditemukan di {output_locations['pentest_output']['path']}",
            success=True,
            context={
                "output_directory": output_locations['pentest_output']['path'],
                "search_pattern": "*.txt"
            }
        )
    
    def train_reading_outputs(self):
        """Train tentang cara membaca output."""
        logger.info("📚 Training: Reading Outputs")
        
        lessons = [
            {
                "lesson": "File output pentest biasanya berisi satu item per line. Gunakan file_system.read untuk membaca, lalu parse per line",
                "context": "Reading pentest output",
                "category": "output_processing",
                "importance": 0.9
            },
            {
                "lesson": "Setelah membaca file output, bisa langsung digunakan sebagai input untuk tool lain (contoh: httpx filter)",
                "context": "Output processing workflow",
                "category": "output_processing",
                "importance": 0.85
            },
            {
                "lesson": "File subdomain biasanya format: satu subdomain per line. Contoh: 'subdomain.example.com'",
                "context": "Subdomain file format",
                "category": "output_processing",
                "importance": 0.8
            },
            {
                "lesson": "File output httpx biasanya berisi URL dengan status code. Format: 'https://subdomain.com [200] [Title]'",
                "context": "httpx output format",
                "category": "output_processing",
                "importance": 0.85
            }
        ]
        
        for lesson_data in lessons:
            self.memory_manager.add_lesson(**lesson_data)
        
        # Experience: Complete read and process workflow
        self.learning_manager.learn_from_task(
            task="Membaca dan memproses output pentest",
            actions=[
                "file_system.read path='pentest_output/subdomains.txt'",
                "Parse output per line",
                "Process dengan tool lain (httpx, dll)"
            ],
            outcome="Berhasil membaca dan memproses output pentest",
            success=True,
            context={
                "workflow": "read_output → parse → process",
                "output_type": "subdomain_list"
            }
        )
    
    def train_pentest_workflows(self):
        """Train tentang pentest workflows."""
        logger.info("📚 Training: Pentest Workflows")
        
        workflows = [
            {
                "name": "Subdomain Enumeration",
                "steps": [
                    "pentest.subdomain_enumeration dengan subfinder",
                    "Output disimpan ke pentest_output/subdomains.txt",
                    "file_system.read untuk membaca hasil",
                    "terminal.execute httpx untuk filter aktif"
                ],
                "task_type": "security_testing"
            },
            {
                "name": "Filter Active URLs",
                "steps": [
                    "file_system.read untuk membaca list subdomain",
                    "terminal.execute httpx dengan input file",
                    "Output disimpan ke pentest_output/active_urls.txt",
                    "file_system.read untuk membaca hasil filter"
                ],
                "task_type": "security_testing"
            },
            {
                "name": "Read Previous Output",
                "steps": [
                    "file_system.list path='pentest_output' untuk melihat file yang ada",
                    "file_system.search pattern='*.txt' untuk mencari semua file output",
                    "file_system.read untuk membaca file yang diinginkan"
                ],
                "task_type": "information_retrieval"
            }
        ]
        
        for workflow in workflows:
            strategy = " → ".join(workflow["steps"])
            self.memory_manager.add_strategy(
                strategy=strategy,
                task_type=workflow["task_type"],
                success_rate=0.9,
                context=f"Workflow: {workflow['name']}"
            )
            
            # Create experience for each workflow
            self.learning_manager.learn_from_task(
                task=f"Workflow: {workflow['name']}",
                actions=workflow["steps"],
                outcome=f"Berhasil menjalankan workflow {workflow['name']}",
                success=True,
                context={
                    "workflow_name": workflow["name"],
                    "task_type": workflow["task_type"]
                }
            )
    
    def train_best_practices(self):
        """Train tentang best practices."""
        logger.info("📚 Training: Best Practices")
        
        best_practices = [
            {
                "lesson": "Selalu verifikasi path sebelum operasi file. Gunakan file_system.list atau file_system.exists untuk check",
                "context": "File operations safety",
                "category": "best_practices",
                "importance": 0.95
            },
            {
                "lesson": "Untuk membaca output pentest, selalu cek dulu direktori pentest_output dengan list, lalu search atau read file spesifik",
                "context": "Reading output files",
                "category": "best_practices",
                "importance": 0.9
            },
            {
                "lesson": "Path untuk file_system tool harus relatif dari workspace root, bukan absolute path. Contoh: 'pentest_output/file.txt'",
                "context": "Path handling",
                "category": "best_practices",
                "importance": 0.95
            },
            {
                "lesson": "Saat menggunakan terminal tool dengan httpx, pastikan input file sudah ada di workspace. Gunakan file_system.read dulu untuk verify",
                "context": "Terminal tool workflow",
                "category": "best_practices",
                "importance": 0.9
            },
            {
                "lesson": "Output file biasanya di workspace/pentest_output/ dengan nama seperti subdomains.txt, active_urls.txt, scan_results.txt",
                "context": "Output file naming",
                "category": "best_practices",
                "importance": 0.85
            },
            {
                "lesson": "Untuk filter dengan httpx, gunakan format: 'httpx -l <input_file> -o <output_file>'. Input file harus ada di workspace",
                "context": "httpx command format",
                "category": "best_practices",
                "importance": 0.9
            }
        ]
        
        for practice in best_practices:
            self.memory_manager.add_lesson(**practice)
    
    def export_training_data(self, output_file: Path, format: str = "json") -> bool:
        """Export training data ke file.
        
        Args:
            output_file: Path ke file output
            format: Format file ('json' atau 'yaml')
            
        Returns:
            True jika berhasil
        """
        try:
            logger.info(f"📤 Exporting training data to {output_file}...")
            
            # Collect all training data
            training_data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "experiences": [],
                "lessons": [],
                "strategies": []
            }
            
            # Export experiences
            if self.memory_manager.vector_memory.available:
                exp_data = self.memory_manager.vector_memory.experiences.get()
                if exp_data and exp_data.get('metadatas'):
                    # Normalize experience data for export
                    for exp in exp_data['metadatas']:
                        # Convert actions_str back to list if needed
                        if 'actions_str' in exp and 'actions' not in exp:
                            actions_str = exp.get('actions_str', '')
                            exp['actions'] = [a.strip() for a in actions_str.split(';') if a.strip()] if actions_str else []
                        training_data["experiences"].append(exp)
                
                # Export lessons
                lesson_data = self.memory_manager.vector_memory.lessons.get()
                if lesson_data and lesson_data.get('metadatas'):
                    training_data["lessons"] = lesson_data['metadatas']
                
                # Export strategies
                strategy_data = self.memory_manager.vector_memory.strategies.get()
                if strategy_data and strategy_data.get('metadatas'):
                    training_data["strategies"] = strategy_data['metadatas']
            
            # Write to file
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "yaml":
                if not YAML_AVAILABLE:
                    logger.warning("PyYAML not installed, falling back to JSON")
                    format = "json"
                else:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        yaml.dump(training_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            if format.lower() == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(training_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Exported {len(training_data['experiences'])} experiences, "
                       f"{len(training_data['lessons'])} lessons, "
                       f"{len(training_data['strategies'])} strategies")
            return True
            
        except Exception as e:
            logger.error(f"❌ Export failed: {e}", exc_info=True)
            return False
    
    def import_training_data(self, input_file: Path, merge: bool = True) -> Dict[str, int]:
        """Import training data dari file.
        
        Args:
            input_file: Path ke file input
            merge: Jika True, merge dengan data existing. Jika False, replace.
            
        Returns:
            Dict dengan jumlah items yang diimport
        """
        try:
            logger.info(f"📥 Importing training data from {input_file}...")
            
            if not input_file.exists():
                raise FileNotFoundError(f"File not found: {input_file}")
            
            # Read file
            content = input_file.read_text(encoding='utf-8')
            
            # Try to parse as YAML first, then JSON
            if YAML_AVAILABLE and (input_file.suffix in ['.yaml', '.yml'] or 'yaml' in content[:100].lower()):
                try:
                    data = yaml.safe_load(content)
                except yaml.YAMLError:
                    data = json.loads(content)
            else:
                data = json.loads(content)
            
            # Validate data structure
            if not isinstance(data, dict):
                raise ValueError("Invalid data format: expected dict")
            
            # Validate and import
            imported = {
                "experiences": 0,
                "lessons": 0,
                "strategies": 0,
                "errors": []
            }
            
            # Import experiences
            if "experiences" in data and isinstance(data["experiences"], list):
                for exp in data["experiences"]:
                    try:
                        if self._validate_experience(exp):
                            # Handle both string and list actions
                            actions = exp.get("actions", [])
                            if not actions and "actions_str" in exp:
                                # Fallback to actions_str if actions not present
                                actions_str = exp.get("actions_str", "")
                                actions = [a.strip() for a in actions_str.split(";") if a.strip()]
                            elif isinstance(actions, str):
                                actions = [a.strip() for a in actions.split(";") if a.strip()]
                            
                            # Extract metadata (exclude fields that are part of experience itself)
                            metadata = exp.get("metadata", {})
                            if not metadata:
                                # If no metadata dict, create one from other fields
                                metadata = {k: v for k, v in exp.items() 
                                          if k not in ["task", "actions", "actions_str", "outcome", "success", "timestamp", "action_count"]}
                            
                            self.memory_manager.add_experience(
                                task=exp.get("task", ""),
                                actions=actions,
                                outcome=exp.get("outcome", ""),
                                success=exp.get("success", True),
                                metadata=metadata
                            )
                            imported["experiences"] += 1
                        else:
                            imported["errors"].append(f"Invalid experience: missing required fields")
                    except Exception as e:
                        imported["errors"].append(f"Failed to import experience: {e}")
            
            # Import lessons
            if "lessons" in data and isinstance(data["lessons"], list):
                for lesson in data["lessons"]:
                    try:
                        if self._validate_lesson(lesson):
                            self.memory_manager.add_lesson(
                                lesson=lesson.get("lesson", ""),
                                context=lesson.get("context", ""),
                                category=lesson.get("category", "general"),
                                importance=lesson.get("importance", 1.0)
                            )
                            imported["lessons"] += 1
                        else:
                            imported["errors"].append(f"Invalid lesson: {lesson}")
                    except Exception as e:
                        imported["errors"].append(f"Failed to import lesson: {e}")
            
            # Import strategies
            if "strategies" in data and isinstance(data["strategies"], list):
                for strategy in data["strategies"]:
                    try:
                        if self._validate_strategy(strategy):
                            self.memory_manager.add_strategy(
                                strategy=strategy.get("strategy", ""),
                                task_type=strategy.get("task_type", "general"),
                                success_rate=strategy.get("success_rate", 1.0),
                                context=strategy.get("context", "")
                            )
                            imported["strategies"] += 1
                        else:
                            imported["errors"].append(f"Invalid strategy: {strategy}")
                    except Exception as e:
                        imported["errors"].append(f"Failed to import strategy: {e}")
            
            logger.info(f"✅ Imported {imported['experiences']} experiences, "
                       f"{imported['lessons']} lessons, "
                       f"{imported['strategies']} strategies")
            
            if imported["errors"]:
                logger.warning(f"⚠️  {len(imported['errors'])} errors during import")
                for error in imported["errors"][:5]:  # Show first 5 errors
                    logger.warning(f"   - {error}")
            
            return imported
            
        except Exception as e:
            logger.error(f"❌ Import failed: {e}", exc_info=True)
            raise
    
    def _validate_experience(self, exp: Dict[str, Any]) -> bool:
        """Validate experience data structure."""
        required = ["task", "outcome"]
        return all(key in exp for key in required)
    
    def _validate_lesson(self, lesson: Dict[str, Any]) -> bool:
        """Validate lesson data structure."""
        required = ["lesson", "context"]
        return all(key in lesson for key in required)
    
    def _validate_strategy(self, strategy: Dict[str, Any]) -> bool:
        """Validate strategy data structure."""
        required = ["strategy", "task_type"]
        return all(key in strategy for key in required)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Train memory system dengan pengetahuan tentang tools dan workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Training semua module
  python train_memory.py
  
  # Training module spesifik
  python train_memory.py --module tools
  
  # Export training data
  python train_memory.py --export training_data.json
  python train_memory.py --export training_data.yaml --format yaml
  
  # Import training data
  python train_memory.py --import training_data.json
  python train_memory.py --import training_data.yaml
        """
    )
    
    # Training mode
    parser.add_argument(
        "--module",
        choices=["all", "tools", "files", "terminal", "outputs", "reading", "pentest", "practices"],
        default="all",
        help="Module training yang akan dijalankan (default: all)"
    )
    
    # Export mode
    parser.add_argument(
        "--export",
        type=str,
        metavar="FILE",
        help="Export training data ke file (JSON atau YAML)"
    )
    
    # Import mode
    parser.add_argument(
        "--import",
        dest="import_file",
        type=str,
        metavar="FILE",
        help="Import training data dari file (JSON atau YAML)"
    )
    
    # Format option
    parser.add_argument(
        "--format",
        choices=["json", "yaml"],
        default="json",
        help="Format file untuk export (default: json)"
    )
    
    # Merge option for import
    parser.add_argument(
        "--merge",
        action="store_true",
        default=True,
        help="Merge dengan data existing saat import (default: True)"
    )
    
    args = parser.parse_args()
    
    trainer = MemoryTrainer()
    
    # Export mode
    if args.export:
        output_file = Path(args.export)
        success = trainer.export_training_data(output_file, format=args.format)
        if success:
            print(f"\n✅ Training data exported to: {output_file}")
            print(f"   Format: {args.format.upper()}")
        else:
            print(f"\n❌ Export failed!")
            sys.exit(1)
        return
    
    # Import mode
    if args.import_file:
        input_file = Path(args.import_file)
        if not input_file.exists():
            print(f"\n❌ File not found: {input_file}")
            sys.exit(1)
        
        result = trainer.import_training_data(input_file, merge=args.merge)
        print(f"\n✅ Import completed!")
        print(f"   Experiences: {result['experiences']}")
        print(f"   Lessons: {result['lessons']}")
        print(f"   Strategies: {result['strategies']}")
        if result.get('errors'):
            print(f"   Errors: {len(result['errors'])}")
        return
    
    # Training mode
    if args.module == "all":
        trainer.train_all()
    elif args.module == "tools":
        trainer.train_tool_usage()
    elif args.module == "files":
        trainer.train_file_operations()
    elif args.module == "terminal":
        trainer.train_terminal_operations()
    elif args.module == "outputs":
        trainer.train_output_locations()
    elif args.module == "reading":
        trainer.train_reading_outputs()
    elif args.module == "pentest":
        trainer.train_pentest_workflows()
    elif args.module == "practices":
        trainer.train_best_practices()
    
    print("\n✅ Training completed!")
    print("\n📊 Memory Statistics:")
    
    # Get statistics directly from memory for accurate count
    memory = trainer.memory_manager.vector_memory
    if memory.available:
        exp_count = memory.experiences.count()
        lesson_count = memory.lessons.count()
        strategy_count = memory.strategies.count()
        
        print(f"   Experiences: {exp_count}")
        print(f"   Lessons: {lesson_count}")
        print(f"   Strategies: {strategy_count}")
        print(f"   Backend: chromadb")
        print(f"   Storage: {memory.persist_directory}")
    else:
        stats = trainer.learning_manager.get_learning_statistics()
        print(f"   Experiences: {stats.get('total_experiences', 0)}")
        print(f"   Lessons: {stats.get('total_lessons', 0)}")
        print(f"   Strategies: {stats.get('total_strategies', 0)}")
        print(f"   Backend: {stats.get('backend', 'unknown')}")
        print(f"   Storage: {stats.get('storage_path', 'N/A')}")
    
    # Get success rate if available
    stats = trainer.learning_manager.get_learning_statistics()
    if stats.get('overall_success_rate', 0) > 0:
        print(f"   Success Rate: {stats.get('overall_success_rate', 0):.1%}")


if __name__ == "__main__":
    main()

