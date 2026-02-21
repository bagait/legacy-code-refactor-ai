# AI-Powered Architectural Refactoring for Legacy Code

This project uses an AI agent to analyze legacy Python codebases. It combines Abstract Syntax Tree (AST) parsing with the reasoning power of a Large Language Model (LLM) to understand the code's structure, identify architectural smells, and propose a refactored, modern design. The tool generates both a textual description of the proposed changes and "before" and "after" architecture diagrams.


*Example 'after' diagram generated for the legacy code sample.*

## Features

- **AST-based Code Analysis**: Uses `tree-sitter` to parse the source code into a concrete syntax tree, reliably extracting function definitions and call graphs.
- **LLM-Powered Suggestions**: Leverages a local LLM (via Ollama) to analyze the code structure and suggest architectural improvements based on software engineering best practices.
- **Structured Output**: The AI provides a summary, detailed reasoning for the changes, and a formal graph description.
- **Before & After Visualization**: Automatically generates diagrams of the current and proposed architectures using `graphviz` for easy comparison.

## How It Works

The process follows three main steps:

1.  **Parse**: The `CodeAnalyzer` uses `tree-sitter` to parse the target Python file. It traverses the Abstract Syntax Tree to identify key structural elements like functions and the calls between them. This information is compiled into a simple JSON structure.
2.  **Suggest**: The `RefactorSuggester` sends this JSON structure to an LLM. A carefully crafted prompt instructs the LLM to act as an expert software architect, analyze the structure for smells (like monolithic functions or poor separation of concerns), and propose a refactored design. The LLM is instructed to return its answer in a structured JSON format, including a Graphviz DOT string for the new architecture.
3.  **Visualize**: The `ArchitectureVisualizer` takes the initial structure and the LLM's proposed DOT string. It uses the `graphviz` library to render two PNG images: `_before.png` showing the original, often tangled, structure, and `_after.png` showing the AI's cleaner, proposed design.

## Installation

This project relies on a few external tools and Python libraries.

**1. System Dependencies**

You must have **Graphviz** installed on your system for diagram rendering.

-   **macOS (via Homebrew):**
    bash
    brew install graphviz
    
-   **Ubuntu/Debian:**
    bash
    sudo apt-get update && sudo apt-get install -y graphviz
    
-   **Windows (via Chocolatey):**
    bash
    choco install graphviz
    

**2. Ollama (for the LLM)**

This tool uses a locally running LLM via [Ollama](https://ollama.com/).

-   Download and install Ollama for your operating system.
-   Pull a model to use for analysis (we recommend `llama3`):
    bash
    ollama pull llama3
    
-   Ensure the Ollama application is running before executing the script.

**3. Python Project Setup**

-   Clone the repository:
    bash
    git clone https://github.com/bagait/legacy-code-refactor-ai.git
    cd legacy-code-refactor-ai
    

-   Create a virtual environment and install dependencies:
    bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    

## Usage

Run the `main.py` script and pass the path to the Python file you want to analyze. The project includes a `legacy_code_example.py` to demonstrate its capabilities.

bash
python main.py legacy_code_example.py


To use a different Ollama model, use the `--model` flag:

bash
python main.py legacy_code_example.py --model mistral


### Expected Output

The script will print the analysis and suggestions to your console. It will also create an `output/` directory with two image files:

-   `output/legacy_code_example_before.png`: A diagram of the original code structure.
-   `output/legacy_code_example_after.png`: A diagram of the AI's proposed new architecture.

**Example Console Output:**


Analyzing legacy code file: legacy_code_example.py
Code analysis complete. Found following structure:
{
  "functions": {
    "process_data_monolith": {
      "calls": []
    }
  },
  "classes": {},
  "global_calls": []
}

Generating 'before' architecture diagram...
✅ Diagram saved to output/legacy_code_example_before.png

Asking the AI architect for refactoring suggestions...

--- AI Architect's Suggestion ---

Summary: The proposed refactoring breaks down the monolithic `process_data_monolith` function into three distinct classes, each with a single responsibility, adhering to the Single Responsibility Principle (SRP). A `DataReader` class will handle reading the CSV, a `DataProcessor` class will manage the business logic of aggregation and filtering, and a `ReportGenerator` class will be responsible for creating the JSON and CSV output files. This creates a clean, decoupled, and more testable architecture.

Reasoning:
- Separation of Concerns: Each part of the process (reading, processing, writing) is now in its own isolated component.
- Testability: Each class can be unit tested independently. You can test the data processing logic without needing a real file system.
- Reusability: The `DataReader` or `ReportGenerator` could be reused in other parts of the application.
- Maintainability: Changes to one part of the logic (e.g., adding a new report format) are less likely to break another.
-----------------------------------

Generating 'after' architecture diagram...
✅ Diagram saved to output/legacy_code_example_after.png


## License

This project is licensed under the MIT License. See the LICENSE file for details.
