# Claude Code Configuration

## Python Commands
Do not run Python commands directly. Instead, provide the user with the commands to run manually.

When testing imports or running Python code, provide the commands like this:

```bash
# Test command example:
python -c "import sys; sys.path.insert(0, 'src'); from game.cv.finger_gun_detection import EnhancedHandTracker; print('Import successful')"
```

## Rationale
- The user prefers to run Python commands themselves
- This prevents unexpected code execution
- Allows the user to control when and how Python code runs
- Better for debugging and understanding what's happening

## Code Comments Policy
- Keep comments informative and clear about functionality
- Do NOT add change tracking comments (e.g., "Fixed - now bigger", "Changed from 15px to 20px")
- Do NOT add parenthetical notes about what was modified (e.g., "Triangles (now larger)")
- Only write comments that describe what the code does, not what changed
- Keep existing comment style unless there's a functional reason to update
- Avoid excessive commenting - let the code speak for itself when obvious

### Avoid These Types of Comments:
- Redundant explanations: `# Set variable to 5` (when code says `variable = 5`)
- Obvious descriptions: `# Update clouds` (before `update_clouds()`)
- AI-generated verbosity: `# Initialize base class (handles camera, hand tracker, sound manager)`
- State-the-obvious: `# Good shot!` (in obvious success case)  
- Overly detailed: `# Calculate max height so flower doesn't extend above ground line`
- Implementation details: `# Using CapybaraManager instead of direct management`
- Buffer explanations: `# Increased from 3 to 5 for buffer`

### Good Comments Explain:
- Business logic and game mechanics
- Complex calculations or algorithms  
- Non-obvious behavior or edge cases
- Important architectural decisions
- "Why" rather than "what"

## Other Tool Usage
- File operations (Read, Write, Edit) are fine
- Bash commands for file system operations are acceptable
- Use TodoWrite for task tracking
- Grep and search tools are encouraged
- CLAUDE.md
- memory CLAUDE.md