# AST Visitor Base Component

Python AST analysis visitor pattern implementations for code quality analysis.

## Features

- BaseConnascenceVisitor for connascence detection
- MagicLiteralVisitor for magic number/string detection
- ParameterPositionVisitor for positional argument checks
- GodObjectVisitor for god object detection
- ComplexityVisitor for cyclomatic complexity

## Usage

```python
import ast
from visitor_base import (
    MagicLiteralVisitor,
    ComplexityVisitor,
    VisitorContext
)

# Parse code
code = '''
def calculate(x):
    return x * 42 + 100
'''
tree = ast.parse(code)

# Create context
context = VisitorContext(
    file_path="module.py",
    source_code=code
)

# Detect magic literals
visitor = MagicLiteralVisitor()
violations = visitor.visit_with_context(tree, context)

for v in violations:
    print(f"Line {v.line}: {v.message}")
# Line 3: Magic literal 42 detected
# Line 3: Magic literal 100 detected

# Calculate complexity
complexity_visitor = ComplexityVisitor()
metrics = complexity_visitor.visit_with_context(tree, context)
print(f"Cyclomatic complexity: {metrics.complexity}")
```

## Visitor Types

| Visitor | Detects | SARIF Level |
|---------|---------|-------------|
| MagicLiteralVisitor | Numbers/strings without names | warning |
| ParameterPositionVisitor | Positional-only params | note |
| GodObjectVisitor | Classes with too many methods | warning |
| ComplexityVisitor | High cyclomatic complexity | warning |

## Extending

Create custom visitors by subclassing `BaseConnascenceVisitor`:

```python
class MyVisitor(BaseConnascenceVisitor):
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Your analysis logic
        if some_condition:
            self.add_violation(
                line=node.lineno,
                message="Issue detected",
                severity="warning"
            )
        self.generic_visit(node)
```
