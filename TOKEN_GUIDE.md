# Token Usage Monitoring Guide

## Usage Patterns to Follow

### Do: Targeted Context
- Use `@filename` for specific files
- Avoid entire directories when possible
- Only include files essential to the task

### Don't: Broad Context
- Avoid "analyze the codebase" prompts
- Don't include test files unless testing
- Skip config files unless modifying them

## Command Usage

Use optimized commands:
- `/test` instead of "run all tests and explain everything"
- `/lint` instead of "check code quality and suggest improvements"

## Agent Usage

- Edit and bash operations now require confirmation
- This prevents runaway token consumption
- Consider each confirmation request carefully

## Monitoring Checklist

Track these metrics:
- [ ] Tokens per request (check provider dashboard)
- [ ] Number of retries per session
- [ ] Context size warnings
- [ ] Most expensive workflows

## Cost Attribution

Log your sessions by task type:
- Code generation vs refactoring vs debugging
- Interactive vs automated usage
- Per project or repository basis

## Optimization Tips

1. **Specific prompts > Broad prompts**
   - "Fix this function" vs "Review this file"

2. **Diffs > Full rewrites**  
   - "Show changes needed" vs "Rewrite this file"

3. **Small model for repetitive tasks**
   - Use `/test` and `/lint` commands
   - Reserve main model for complex reasoning

4. **Context management**
   - Clear session history when starting new tasks
   - Restart OpenCode if context becomes too large