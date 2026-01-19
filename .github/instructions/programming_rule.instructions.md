---
applyTo: "**"
---

# Global Programming Rules
- Everything must be written in English.
- Emojis must never be used.

## Function Design
- The length of a single function must not exceed 60 lines.
- A function must perform only a single responsibility.
- Code that is used repeatedly must be extracted into reusable functions.
- A function should operate at a single level of abstraction.
- The number of function parameters should be kept to a minimum.
- Argument and return types must be explicitly specified.
- Avoid complex coding techniques; use simple and straightforward syntax.
- Indentation must not be nested more than two levels deep.
- Use early returns to reduce nested control structures.
- Each function must include at least two assertions that explicitly validate critical assumptions or invariants.
-	Assertions must check meaningful preconditions, postconditions, or internal invariants, not trivial or redundant conditions.
-	Assertions must not be used as a replacement for proper error handling in production paths.

## Naming Conventions
- Names must clearly express intent and responsibility.
- Avoid abbreviations unless they are widely and commonly understood.
- Function names should start with verbs.
- Class and type names should be nouns.
- Boolean variables should use prefixes such as is, has, or can.

## Code Readability
- Code should be written in a clear, readable, and consistent style.
- Prefer positive conditions over negative ones in conditional statements.
- Complex conditional expressions must be extracted into well-named variables or functions.
- Avoid magic numbers; define constants with meaningful names instead.
- Write one logical idea per line.
- Keep line length within a reasonable limit (e.g., 100–120 characters).
- Use blank lines to separate logical sections of code.

## Comments and Documentation
- Comments should be minimized and avoided whenever possible.
- Do not comment on what the code does; comment only on why it exists when necessary.
- Public APIs, interfaces, and boundaries may include brief documentation comments.

## Control Flow and Error Handling
- Reduce the use of else by structuring code with clear and explicit branches.
- Do not silently ignore errors.
- Clearly separate error-handling logic from normal execution paths.
- Prefer explicit error types or mechanisms over implicit error signaling.

## Modularity and Dependencies
- Organize code into well-defined, cohesive modules.
- Dependencies must flow in a single direction.
- Circular dependencies are not allowed.
- Minimize reliance on global state; define clear ownership when unavoidable.
- Depend on abstractions or interfaces rather than concrete implementations.
- Isolate external libraries behind dedicated layers.

## Testability and Maintainability
- Design code to be easy to test, especially in areas that change frequently.
- Limit side effects to well-defined boundaries.
- Code should be structured so that the impact of changes is predictable.
- Code that is difficult to test should be considered a maintenance risk.

## Logging
- Logging must be used sparingly and intentionally.
- Logs should exist only at meaningful boundaries or critical decision points.
- Do not log information that can be inferred directly from code flow.
- Avoid repetitive, verbose, or low-value logs.
- Logs must improve understanding of system behavior, not add noise.
- Logging must never be used as a substitute for proper error handling.
- Log messages must be clear, concise, and written in plain language.
- Avoid logging inside tight loops or high-frequency execution paths.
- Sensitive or unnecessary internal details must not be logged.
- The absence of a log should be the default; add logs only when they provide clear diagnostic value.
