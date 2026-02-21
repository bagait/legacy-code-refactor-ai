import argparse
import json
import os
from pathlib import Path
import sys

try:
    from tree_sitter import Language, Parser
    from tree_sitter_languages import get_language, get_parser
    from langchain_community.chat_models import ChatOllama
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    import graphviz
except ImportError:
    print("Dependencies not found. Please run 'pip install -r requirements.txt'")
    sys.exit(1)

# --- 1. Code Analyzer (using tree-sitter) ---

class CodeAnalyzer:
    """Parses Python code to extract its high-level structure using tree-sitter."""

    def __init__(self):
        """Initializes the tree-sitter parser for Python."""
        try:
            self.language = get_language('python')
        except Exception as e:
            print(f"Error getting tree-sitter language: {e}")
            print("Please ensure tree-sitter grammars are correctly installed.")
            sys.exit(1)
        self.parser = Parser()
        self.parser.set_language(self.language)

    def _execute_query(self, tree, query_string):
        """Helper to run a tree-sitter query and return captures."""
        query = self.language.query(query_string)
        captures = query.captures(tree.root_node)
        return captures

    def analyze(self, file_path):
        """Analyzes a Python file to extract functions, classes, and their calls."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
            return None

        tree = self.parser.parse(bytes(code, "utf8"))

        structure = {
            "functions": {},
            "classes": {},
            "global_calls": []
        }

        # Query for function definitions
        func_query = "(function_definition name: (identifier) @function.name)"
        functions = self._execute_query(tree, func_query)
        for node, name in functions:
            if name == "function.name":
                func_name = node.text.decode('utf8')
                structure["functions"][func_name] = {"calls": []}

        # Query for calls inside functions
        call_query = """
        (function_definition
            name: (identifier) @function.name
            body: (_
                (call
                    function: (attribute attribute: (identifier) @method.name) 
                ) @call
                |
                (call 
                    function: (identifier) @function.call
                ) @call
            )
        )
        """
        calls = self._execute_query(tree, call_query)
        current_func = None
        for node, name in calls:
            if name == "function.name":
                current_func = node.text.decode('utf8')
            elif name in ["function.call", "method.name"] and current_func:
                call_name = node.text.decode('utf8')
                if current_func in structure["functions"]:
                    structure["functions"][current_func]["calls"].append(call_name)

        return structure


# --- 2. Refactor Suggester (using LangChain and Ollama) ---

class RefactorSuggester:
    """Uses an LLM to suggest refactoring based on code structure."""

    def __init__(self, model_name="llama3"):
        """Initializes the LangChain model and prompt template."""
        self.prompt = ChatPromptTemplate.from_template("""
        You are an expert software architect specializing in refactoring legacy Python code.
        Your task is to analyze the provided code structure and propose a modern, cleaner architecture.
        Focus on SOLID principles, separation of concerns, and creating maintainable code.

        Here is the high-level structure of a legacy Python script:
        {code_structure}

        Based on this structure, please provide a refactoring suggestion.
        Your output MUST be a single, valid JSON object with the following keys:
        - "summary": A high-level, one-paragraph description of the proposed refactoring.
        - "reasoning": A bullet-point list explaining why this refactoring is beneficial (e.g., improves separation of concerns, follows SOLID principles).
        - "new_architecture_dot": A string containing the proposed new architecture in Graphviz DOT format. The graph should show new classes/modules and their relationships. Use a 'TB' rankdir. Give nodes a rounded box shape. Cluster related components.

        Example for `new_architecture_dot`:
        "digraph Refactored {{
            rankdir=TB;
            node [shape=box, style=rounded];
            subgraph cluster_data {{
                label = \"Data Handling\";
                DataReader [label=\"DataReader\\n(reads_csv)\"];
                ReportGenerator [label=\"ReportGenerator\\n(write_json, write_csv)\"];
            }}
            main -> DataReader;
            DataReader -> Processor [label=\"raw_data\"];
        }}"

        Now, generate the JSON for the provided code structure.
        """)
        try:
            self.model = ChatOllama(model=model_name)
        except Exception as e:
            print(f"Error initializing Ollama model '{model_name}': {e}")
            print("Please ensure Ollama is running and the specified model is available ('ollama run llama3').")
            sys.exit(1)
            
        self.chain = self.prompt | self.model | StrOutputParser()

    def suggest(self, code_structure):
        """Generates a refactoring suggestion from the LLM."""
        print("\nAsking the AI architect for refactoring suggestions...")
        structure_str = json.dumps(code_structure, indent=2)
        response = self.chain.invoke({"code_structure": structure_str})
        try:
            # Clean the response to ensure it's valid JSON
            # LLMs sometimes add markdown fences ... 
            clean_response = response.strip().replace("", "").replace("", "")
            return json.loads(clean_response)
        except json.JSONDecodeError:
            print("Error: Could not decode the LLM's JSON response.")
            print("--- Raw LLM Output ---")
            print(response)
            print("-----------------------")
            return None


# --- 3. Architecture Visualizer (using graphviz) ---

class ArchitectureVisualizer:
    """Generates diagrams from code structures or DOT strings."""

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def _render_graph(self, graph, filename):
        """Renders a graphviz object to a file."""
        output_path = self.output_dir / filename
        try:
            graph.render(output_path, format='png', cleanup=True)
            print(f"✅ Diagram saved to {output_path}.png")
        except graphviz.backend.execute.ExecutableNotFound:
            print("\nError: 'graphviz' executable not found.")
            print("Please install Graphviz on your system.")
            print("  - macOS: brew install graphviz")
            print("  - Ubuntu/Debian: sudo apt-get install graphviz")
            print("  - Windows: choco install graphviz")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred during graph rendering: {e}")

    def generate_from_structure(self, code_structure, filename):
        """Creates a 'before' diagram from the initial analysis."""
        dot = graphviz.Digraph('Legacy_Architecture', comment='Original Code Structure')
        dot.attr('node', shape='box', style='rounded')
        dot.attr(label='Original Architecture', labelloc='t', fontsize='16')

        for func, details in code_structure.get('functions', {}).items():
            dot.node(func, f"{func}()")
            for call in details.get('calls', []):
                # Only draw edges to functions defined in the file
                if call in code_structure['functions']:
                    dot.edge(func, call)
        
        if not dot.body:
            print("No defined functions found to visualize in the original structure.")
            return

        self._render_graph(dot, filename)

    def generate_from_dot_string(self, dot_string, filename):
        """Renders the LLM-provided DOT string for the 'after' diagram."""
        try:
            graph = graphviz.Source(dot_string)
            self._render_graph(graph, filename)
        except Exception as e:
            print(f"Error rendering DOT string: {e}")
            print("--- Invalid DOT string ---")
            print(dot_string)
            print("------------------------")


# --- Main execution block ---

def main(file_path, model):
    """The main orchestration function."""
    print(f"Analyzing legacy code file: {file_path}")
    target_name = Path(file_path).stem

    # 1. Analyze the code
    analyzer = CodeAnalyzer()
    code_structure = analyzer.analyze(file_path)
    if not code_structure:
        return

    print("Code analysis complete. Found following structure:")
    print(json.dumps(code_structure, indent=2))

    # 2. Visualize the 'before' architecture
    visualizer = ArchitectureVisualizer(output_dir='output')
    print("\nGenerating 'before' architecture diagram...")
    visualizer.generate_from_structure(code_structure, f"{target_name}_before")

    # 3. Get refactoring suggestion from LLM
    suggester = RefactorSuggester(model_name=model)
    suggestion = suggester.suggest(code_structure)

    if not suggestion:
        print("Could not get a valid suggestion from the LLM. Exiting.")
        return

    # 4. Print textual suggestion
    print("\n--- AI Architect's Suggestion ---")
    print(f"\nSummary: {suggestion.get('summary', 'N/A')}")
    print("\nReasoning:")
    reasoning = suggestion.get('reasoning', ['N/A'])
    if isinstance(reasoning, list):
        for point in reasoning:
            print(f"- {point}")
    else:
        print(reasoning)
    print("-----------------------------------")

    # 5. Visualize the 'after' architecture
    dot_string = suggestion.get('new_architecture_dot')
    if dot_string:
        print("\nGenerating 'after' architecture diagram...")
        visualizer.generate_from_dot_string(dot_string, f"{target_name}_after")
    else:
        print("\nWarning: No DOT string for 'after' diagram found in the LLM response.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Use an AI agent to analyze and suggest refactoring for legacy Python code."
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the legacy Python file to analyze."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama3",
        help="The name of the Ollama model to use (e.g., 'llama3', 'mistral')."
    )
    args = parser.parse_args()
    main(args.file_path, args.model)
