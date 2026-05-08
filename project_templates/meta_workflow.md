**Step 0: get setup**
    - project folder – with topic subfolders that your projects will be organized under
    - setup uv, claude code (user-wide CLAUDE.md)
        - alignment hive helps

**Step 1: have an idea, think about how to tell Claude**
    - create project folder for your new idea, uv init
    - create README.md and CLAUDE.md (mention knowledge base if you have one, or other things a new Claude instance should read)
    - create docs subfolder, and docs/papers
    - create docs/planning.md - write a proj desc (potentially by having a web chat w Claude about your idea and then asking for a project plan)

**Step 2: Claude Code**
    - launch Claude Code in your new project folder
    - ask Claude to read planning doc and do basic setup
        - often it's helpful to start in planning mode, and then graduate to auto mode

**Step 3: The Loop**
    a. Research on web – (potentially using lit-review skill from alignment hive)
        - insist that all sources be saved to docs/papers (papers, blog posts, twitter posts, prophetic dreams, whatever)
        - tell Claude to write research notes and save as markdown in docs

    b. Plan – create or add to MASTER_PLAN.md
        - include a ToDo List

    c. Work on Next Item from ToDo
        c1. Implement Code
        c2. write unit tests & run smoke test
        c3. trial run (limit 3-5 hours)
            - bugs inevitably emerge
            - in ML it is often the case that bugs are subtle, so you have to assume some exist and test defensively
            - start with known toy tasks; overfit a tiny batch first; assert tensor shapes; eyeball loss curves immediately; check for silent NaN or overflow

    d. Log - you and Claude should document learnings and progress. 
        - Better to take too many notes than too few, it's easy to search but hard to remember.
        - Keep a research_journal.md in docs and remind Claude to keep adding to it
        - Save runs and logs to a datestamped run folder in outputs. Make sure you save stderr to your logs, so you can diagnose crashes.
        - Make config be source of truth and copy it into the run folder at beginning of run. Use that config to resume the run.

    e. Loop back to appropriate step
        e1. if you have more ToDos, go to c
        e2. if you are out of ToDo items, but have research not yet turned into todo items, go to b
        e3. if you need more ideas to turn into ToDo items, go to a
        e4. if you've hit a dead-end go back to Step 1

**Step 4: Scale**
    - Once you've done a bunch of loops and your project is well detailed and tested, it's time to scale. 
    - This commits substantial time, effort and compute resources so don't jump to this step prematurely!
    - Estimate your needed compute, spend some time looking for efficiency improvements
    - Make sure you setup checkpoint saving, soft-stop, and resuming from checkpoints
    - Make sure you setup proper monitoring (e.g. wandb). Be prepared to rollback to earlier checkpoints if things go wrong.

**Step 5: Analyze and writeup**
    - understand your results
    - communicate your results