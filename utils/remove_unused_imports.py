#!/usr/bin/env python3
"""
Oracle - Remove Unused Imports
File: utils/remove_unused_imports.py

A comprehensive script to remove all unused imports from the entire project.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unused_imports_removal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ImportInfo:
    """Information about an import statement."""
    line_number: int
    import_statement: str
    module_name: str
    imported_names: List[str]
    is_used: bool = False

@dataclass
class FileImportAnalysis:
    """Analysis results for a single file."""
    file_path: str
    total_imports: int
    unused_imports: int
    imports_info: List[ImportInfo]
    content_after_cleaning: str = ""

class UnusedImportsRemover:
    """Comprehensive unused imports removal tool."""
    
    def __init__(self, project_root: str = "."):
        """Initialize the unused imports remover."""
        self.project_root = Path(project_root).resolve()
        self.python_files = []
        self.analysis_results = {}
        
        # Define file patterns to analyze
        self.include_patterns = ["*.py"]
        self.exclude_patterns = [
            "__pycache__", "*.pyc", "*.pyo", "*.pyd",
            ".git", ".venv", "venv", "env", "node_modules",
            "build", "dist", "*.egg-info"
        ]
        
        logger.info(f"Initialized Unused Imports Remover for {self.project_root}")
    
    def discover_python_files(self) -> List[Path]:
        """Discover all Python files in the project."""
        logger.info("Discovering Python files...")
        python_files = []
        
        for pattern in self.include_patterns:
            for file_path in self.project_root.rglob(pattern):
                # Check if file should be excluded
                if any(exclude in str(file_path) for exclude in self.exclude_patterns):
                    continue
                
                if file_path.is_file():
                    python_files.append(file_path)
        
        self.python_files = sorted(python_files)
        logger.info(f"Found {len(self.python_files)} Python files to analyze")
        return self.python_files
    
    def extract_imports(self, file_path: Path) -> List[ImportInfo]:
        """Extract all import statements from a file."""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # Handle: import module
                    for alias in node.names:
                        import_info = ImportInfo(
                            line_number=node.lineno,
                            import_statement=f"import {alias.name}",
                            module_name=alias.name.split('.')[0],
                            imported_names=[alias.name.split('.')[0]]
                        )
                        imports.append(import_info)
                
                elif isinstance(node, ast.ImportFrom):
                    # Handle: from module import name1, name2
                    module_name = node.module or ""
                    imported_names = []
                    
                    for alias in node.names:
                        imported_names.append(alias.name)
                    
                    # Create import statement
                    if node.level > 0:
                        # Relative import
                        dots = "." * node.level
                        import_statement = f"from {dots}{module_name} import {', '.join(imported_names)}"
                    else:
                        import_statement = f"from {module_name} import {', '.join(imported_names)}"
                    
                    import_info = ImportInfo(
                        line_number=node.lineno,
                        import_statement=import_statement,
                        module_name=module_name.split('.')[0] if module_name else "",
                        imported_names=imported_names
                    )
                    imports.append(import_info)
        
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
        
        return imports
    
    def find_used_names(self, file_path: Path) -> Set[str]:
        """Find all used names in a file."""
        used_names = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Load):
                        used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    # Handle attribute access like module.function
                    if isinstance(node.value, ast.Name):
                        used_names.add(node.value.id)
        
        except Exception as e:
            logger.warning(f"Error analyzing used names in {file_path}: {e}")
        
        return used_names
    
    def analyze_file_imports(self, file_path: Path) -> FileImportAnalysis:
        """Analyze imports in a single file."""
        logger.info(f"Analyzing imports in {file_path}")
        
        imports_info = self.extract_imports(file_path)
        used_names = self.find_used_names(file_path)
        
        # Mark imports as used/unused
        for import_info in imports_info:
            for imported_name in import_info.imported_names:
                if imported_name in used_names:
                    import_info.is_used = True
                    break
        
        unused_count = sum(1 for imp in imports_info if not imp.is_used)
        
        analysis = FileImportAnalysis(
            file_path=str(file_path),
            total_imports=len(imports_info),
            unused_imports=unused_count,
            imports_info=imports_info
        )
        
        return analysis
    
    def remove_unused_imports_from_file(self, file_path: Path, analysis: FileImportAnalysis) -> str:
        """Remove unused imports from a file and return the cleaned content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            lines_to_remove = set()
            
            # Find lines to remove
            for import_info in analysis.imports_info:
                if not import_info.is_used:
                    lines_to_remove.add(import_info.line_number - 1)  # Convert to 0-based index
            
            # Remove unused import lines
            cleaned_lines = []
            for i, line in enumerate(lines):
                if i not in lines_to_remove:
                    cleaned_lines.append(line)
                else:
                    logger.info(f"Removing unused import: {line.strip()}")
            
            # Clean up consecutive empty lines
            final_lines = []
            prev_empty = False
            
            for line in cleaned_lines:
                if line.strip() == "":
                    if not prev_empty:
                        final_lines.append(line)
                    prev_empty = True
                else:
                    final_lines.append(line)
                    prev_empty = False
            
            return '\n'.join(final_lines)
        
        except Exception as e:
            logger.error(f"Error removing unused imports from {file_path}: {e}")
            return content
    
    def clean_all_files(self) -> Dict[str, FileImportAnalysis]:
        """Clean unused imports from all files."""
        logger.info("Starting unused imports removal process...")
        
        self.discover_python_files()
        results = {}
        total_unused_removed = 0
        
        for file_path in self.python_files:
            try:
                # Analyze the file
                analysis = self.analyze_file_imports(file_path)
                
                if analysis.unused_imports > 0:
                    # Remove unused imports
                    cleaned_content = self.remove_unused_imports_from_file(file_path, analysis)
                    analysis.content_after_cleaning = cleaned_content
                    
                    # Write back the cleaned content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    
                    total_unused_removed += analysis.unused_imports
                    logger.info(f"Removed {analysis.unused_imports} unused imports from {file_path}")
                
                results[str(file_path)] = analysis
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        logger.info(f"Total unused imports removed: {total_unused_removed}")
        return results
    
    def generate_report(self, results: Dict[str, FileImportAnalysis]) -> None:
        """Generate a comprehensive report of the cleaning process."""
        report_path = self.project_root / "UNUSED_IMPORTS_REPORT.md"
        
        total_files = len(results)
        files_with_unused = sum(1 for analysis in results.values() if analysis.unused_imports > 0)
        total_imports = sum(analysis.total_imports for analysis in results.values())
        total_unused = sum(analysis.unused_imports for analysis in results.values())
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Unused Imports Removal Report\n\n")
            f.write(f"**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- **Total Files Analyzed:** {total_files}\n")
            f.write(f"- **Files with Unused Imports:** {files_with_unused}\n")
            f.write(f"- **Total Imports Found:** {total_imports}\n")
            f.write(f"- **Total Unused Imports Removed:** {total_unused}\n")
            cleanup_percentage = (total_unused/total_imports*100) if total_imports > 0 else 0
            f.write(f"- **Cleanup Percentage:** {cleanup_percentage:.1f}%\n\n")
            
            f.write("## File-by-File Analysis\n\n")
            
            for file_path, analysis in results.items():
                if analysis.unused_imports > 0:
                    f.write(f"### {file_path}\n")
                    f.write(f"- **Total Imports:** {analysis.total_imports}\n")
                    f.write(f"- **Unused Imports Removed:** {analysis.unused_imports}\n")
                    f.write(f"- **Remaining Imports:** {analysis.total_imports - analysis.unused_imports}\n\n")
                    
                    f.write("**Removed Imports:**\n")
                    for import_info in analysis.imports_info:
                        if not import_info.is_used:
                            f.write(f"- Line {import_info.line_number}: `{import_info.import_statement}`\n")
                    f.write("\n")
        
        logger.info(f"Report generated: {report_path}")
    
    def run_cleaning_process(self) -> None:
        """Run the complete unused imports cleaning process."""
        logger.info("Starting unused imports cleaning process...")
        
        # Clean all files
        results = self.clean_all_files()
        
        # Generate report
        self.generate_report(results)
        
        # Summary
        total_unused = sum(analysis.unused_imports for analysis in results.values())
        logger.info(f"Unused imports cleaning completed!")
        logger.info(f"Total unused imports removed: {total_unused}")

def main():
    """Main entry point for the unused imports remover."""
    remover = UnusedImportsRemover()
    remover.run_cleaning_process()

if __name__ == "__main__":
    main() 
