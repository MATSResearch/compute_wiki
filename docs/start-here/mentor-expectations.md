---
tags:
  - meta
---

# Understanding "Research Skillz" in light of MATS Mentor expectations

aka how to git gud fast

*By Nathan Helm-Burger.*

I would love to teach you how to have good "Research Taste", but I can't. Good Research Taste means being someone like Ryan Greenblatt or Owain Evans who can pick a series of experiments to do that lead to fascinating discoveries. That takes years of practice and study, plus some kind of innate talent and disposition. What I will focus on in this essay is how to go from a "competent individual contributor" to an "independent self-guided researcher".

Some people come into a fellowship like MATS or a graduate school program with strong technical skills and not a lot of independent research background. These people tend to not be as appealing to Mentors as one might expect given their skillsets. I think part of the problem is about a mismatch in expectations about what Mentors may be hoping for and expecting, versus what, for instance, a direct manager in an industry job context would be looking for.

As someone who has spent quite a few years in both graduate school and industry, here's some of the differences I see.

## In industry:

I would have a brief check-in at the beginning of each day, maybe 5-10 minutes, where I would tell my manager what I had accomplished from the previous day's task list and what I intended to work on today. If they wanted me to reprioritize, they would let me know. If I was blocked on anything, they would tell me who to talk to to get unblocked or unblock me themselves. We would have quarterly planning meetings where we set big goals, and weekly sprint planning meetings where we took a piece of the current big goal and broke it down into tickets that would each take between 1 - 8 hours. Those tickets would be the tasks I would report on each morning.

In other words, a lot of quite close interaction and frequent reprioritization. A high bandwidth relationship. This is quite valuable in getting the maximum possible amount of useful work out of varying skill levels of people. Even when we brought quite junior people onto the team, with this sort of daily oversight we were able to guide them to contribute effectively. This also made it clear what expectations were during a given week, and if I got done with my work early (which happened maybe one week out of 12), then I would have the opportunity to pull a 'blue sky' ticket from the backlog which was a non-assigned project I'd been wanting to work on that I thought was a low-chance-of-working-but-high-value-and-interesting-to-try thing.

The downside of this management style is that it requires a lot of time and focused effort from the manager. They are more like a collaborator on the project than they are an 'advisor'. They are sometimes doing direct work themselves, probably are at least reviewing the code or other products you are producing closely. They don't have the capacity to do projects themselves and also manage ten different projects. They are managing one project, or maybe two, and not directly contributing all that much. That's the expectation, and it results in a well-coordinated team that can pivot rapidly with the wisdom of a collective intelligence rather than trusting each individual worker to have good 'taste' for what the company most needs that week. I felt like I was a strong and capable hand attached to the arm of a giant robot. The robot moved me, and I was trusted to do what was needed wherever I was put.

## In academia (and some non-profit work):

My advisors would be overseeing many different people working on many different projects (at least 5-10, sometimes more like 20), as well as working directly on multiple projects of their own. They would have time to talk to me for maybe half an hour a month. During that time, they'd expect that I'd give them a high level summary of everything I'd done since the last meeting, and get high level direction from them about how to spend my next month. They would entrust me to manage all the things about taking a month long task and breaking it into weekly pieces, and then breaking weekly pieces down into sub-day tasks. They would also expect that if I ran into any blockers, I would independently find my way around them. If I got results partway through that indicated I should pivot to a different line of research, I would be responsible for making that pivot and they would need to trust that I could make a good decision about where to go next even though I hadn't had a discussion with them about it yet. If they thought I would make a poor decision under such circumstances, then they would worry that I might waste weeks worth of work on a dead end.

In MATS, we try to scaffold people (e.g. with research manager support) into being able to go from being 'daily oversight workers' to 'weekly oversight workers', but the eventual goal (and the expectation of future opportunities like the extension) is that Mentors would be able to trust you to become a 'monthly oversight worker'.

So part of what the Mentor is asking themselves while looking at what you've accomplished over the past week is the question, "If I had left this person alone for a month instead of just a week, do I trust that they would have gotten well-directed effective work done, dynamically routed themselves around blockers, pivoted to useful new directions as needed?"

You are expected to be a whole independent robot, sending back occasional reports as you scout and map novel territory. A single arm laying on the ground, no matter how strong and capable, would not be very useful as an independent cartographer. If you send a robot cartographer off on a long journey by foot with the instruction to map an unknown land, you want to be confident that the robot won't get stuck in dead-ends or bogs. That's actually much more important than exactly how fast and strong the robot is, or even how far and accurately it can see. You would like all those qualities, but the most critical one is whether you can trust the robot to work on its own. The robot needs to cover the unknown territory, documenting it in a reliable way, such that when you look at the resulting map you can trust what the map says.

## Further reading: becoming a monthly-oversight researcher

Each of these covers one piece of what a Mentor is checking for when they ask whether they could leave you alone for a month.

### Sakana AI, "An Unofficial Guide to Prepare for a Research Position Application"

[pub.sakana.ai/Unofficial_Guide](https://pub.sakana.ai/Unofficial_Guide/) — Sakana AI, 2026.

Written for people interviewing at Sakana AI, but the qualities it lists are what a MATS Mentor reads in your weekly update: asking the question that distills a vague problem, scoping a prototype to your riskiest assumption, explaining each decision as "I tried X because I expected Y; I observed Z", and stating conclusions first. Its warning that "in 2026 it is surprisingly easy to seem creative" and that unactionable ideas are worthless matches the research evidence that LLM-generated ideas look good on paper and lose much of their value once executed ([`researcher-skills.md`](researcher-skills.md)).

### Eliezer Yudkowsky, "Positive Bias: Look Into the Dark"

[LessWrong](https://www.lesswrong.com/s/5uZQHpecjn7955faL/p/rmAbiEKQDpDnZzcRf) — 2007.

Wason's 2-4-6 task: people test cases they expect to pass, so they never discover the rule is simpler than they think. An independent researcher has no manager catching this for them; the habit to build is designing the test you expect to say "No". It matters more when an AI agent runs your experiments, because agents show the same bias — they mostly confirm, and often ship results their own review flagged.

### Jacob Steinhardt, "Research as a Stochastic Decision Process"

[cs.stanford.edu/~jsteinhardt](https://cs.stanford.edu/~jsteinhardt/ResearchasaStochasticDecisionProcess.html)

How to order the parts of a project yourself, which is the planning a daily manager used to do for you. Do the most informative step per unit time first (sort by failure rate, λ = log(1/p) / t for success probability p and duration t), de-risk before executing, use ceilings, baselines and brute force, and rule out whole approaches rather than single implementations. Also: log estimated vs actual task times to get calibrated within a few weeks.

### Mike Winer, "How to Choose a Subproblem"

[millicosm.substack.com](https://millicosm.substack.com/p/how-to-choose-a-subproblem) — July 2026.

How to "peel the next 20-hour problem off of a 400-hour problem" — the month-into-weeks-into-days breakdown that Mentors expect you to do alone. Three ways to make a subproblem (simpler question, simpler system, fact-finding), red flags for subproblems that are too vague, too hard or too easy, and when to ask someone else whether to quit. Winer explicitly argues against Steinhardt's fail-early rule: it fits projects with several must-win steps where partial work is worthless, while most projects reward patching an approach rather than abandoning it. Read the two together and decide which shape your project has.

---

Last verified: 2026-10. Essay by Nathan Helm-Burger. The reading-list notes were drafted by Claude.
