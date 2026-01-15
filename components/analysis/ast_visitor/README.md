# AST Visitor Base Component

Extended AST visitor with violation collection, path tracking, and pattern matching for code analysis.

## Features

- Enhanced NodeVisitor with context tracking
- Automatic violation collection using `common/types`
- Scope chain and path tracking
- Pattern matching helpers
- NodeTransformer for modifications
- Composite visitor pattern

## Usage

### Basic Analysis Visitor

```python
from library.components.analysis.ast_visitor import (
    AnalysisVisitor,
    visit_file,
)
from library.common.types import Severity

class ComplexityChecker(AnalysisVisitor):
    def visit_FunctionDef(self, node):
        # Check function length
        if len(node.body) > 50:
            self.add_violation(
                severity=Severity.HIGH,
                message=f"Function '{node.name}' has {len(node.body)} statements",
                node=node,
                rule_id="FUNC-TOO-LONG",
                suggestion="Break into smaller functions",
            )

        # Check argument count
        if len(node.args.args) > 5:
            self.add_violation(
                severity=Severity.MEDIUM,
                message=f"Function '{node.name}' has too many parameters",
                node=node,
            )

        # Continue visiting children
        self.generic_visit(node)

# Analyze a file
violations = visit_file("my_code.py", ComplexityChecker)
for v in violations:
    print(f"{v.severity.value}: {v.message} at line {v.line}")
```

### Context Tracking

```python
class ScopeAwareChecker(AnalysisVisitor):
    def visit_Name(self, node):
        # Access current scope information
        print(f"Name '{node.id}' in scope: {self.context.scope_path}")
        print(f"Current class: {self.context.current_class}")
        print(f"Current function: {self.context.current_function}")
        print(f"Nesting depth: {self.context.depth}")
        self.generic_visit(node)
```

### Composite Visitor

Run multiple analyzers in one pass:

```python
from library.components.analysis.ast_visitor import CompositeVisitor

composite = CompositeVisitor([
    ComplexityChecker(),
    SecurityScanner(),
    StyleChecker(),
])

composite.visit(tree)

# All violations aggregated
for v in composite.violations:
    print(v.message)
```

### Converting to QualityResult

```python
from library.common.types import QualityResult

visitor = ComplexityChecker(file_path="my_code.py")
visitor.visit(tree)

# Get QualityResult with computed score
result: QualityResult = visitor.to_quality_result(threshold=0.8)

print(f"Passed: {result.passed}")
print(f"Score: {result.score:.2f}")
print(f"Critical: {result.critical_count}, High: {result.high_count}")
```

### AST Transformer

```python
from library.components.analysis.ast_visitor import AnalysisTransformer
import ast

class RemoveAsserts(AnalysisTransformer):
    def visit_Assert(self, node):
        self.log_modification("Removed assert statement", node)
        return None  # Remove the node

transformer = RemoveAsserts()
new_tree = transformer.visit(tree)
print(f"Modifications: {transformer.modifications}")
```

### Pattern Matchers

```python
from library.components.analysis.ast_visitor import (
    is_name,
    is_call,
    is_method_call,
    get_assigned_name,
    count_nodes,
)

# Check patterns
if is_call(node, "print"):
    print("Found print call")

if is_method_call(node, "self", "save"):
    print("Found self.save() call")

# Count nodes
num_functions = count_nodes(tree, ast.FunctionDef)
```

## API Reference

### AnalysisVisitor

Base class for code analysis with violation collection.

```python
class AnalysisVisitor(ast.NodeVisitor):
    context: VisitorContext      # Current traversal context
    violations: List[Violation]  # Collected violations

    def add_violation(
        severity: Union[str, Severity],
        message: str,
        node: Optional[ast.AST] = None,
        rule_id: Optional[str] = None,
        suggestion: Optional[str] = None,
        **metadata,
    )

    def to_quality_result(
        score: Optional[float] = None,
        threshold: float = 0.8,
    ) -> QualityResult
```

### VisitorContext

```python
@dataclass
class VisitorContext:
    file_path: Optional[str]
    scope_chain: List[str]
    current_class: Optional[str]
    current_function: Optional[str]
    depth: int
    visited_nodes: int
    scope_path: str  # Property: dotted scope path

    def push_scope(name: str)
    def pop_scope() -> Optional[str]
```

### Helper Functions

```python
parse_file(file_path) -> ast.Module
parse_source(source, filename?) -> ast.Module
visit_file(file_path, visitor_class, **kwargs) -> List[Violation]
visit_source(source, visitor_class, **kwargs) -> List[Violation]
```

## LEGO Compatibility

This component imports from `library/common/types`:
- `Severity` - Violation severity levels
- `Violation` - Violation data structure
- `QualityResult` - Analysis result with violations

## Sources

- [Python ast module](https://docs.python.org/3/library/ast.html)
- [LibCST](https://github.com/Instagram/LibCST)
- [ast.NodeVisitor documentation](https://tedboy.github.io/python_stdlib/generated/generated/ast.NodeVisitor.html)
