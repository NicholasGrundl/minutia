"""
Meeting summary prompts.

Orthogonal collection of prompt builders used to drive
`minutia.steps.summarize_transcript.generate_long_summary`. Mirrored from
the inline prompt cells in `notebooks/20260514_MasterTrackTranscription.ipynb`
so they can be imported once a flavor has proven itself in notebook
experiments.

Not yet imported by the notebook or by `summarize_transcript.py`; safe to
edit without affecting the running pipeline.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

PromptBuilder = "callable[[str, str], str]"


def realty_summary_prompt(markdown_notes: str = "", personal_info: str = "") -> str:
    """Real-estate-focused meeting summary prompt."""
    return f"""# 🏠 Real Estate Meeting Summary Generator

#CONTEXT: Your task is to create a clear, actionable summary of a meeting with a real estate agent about buying a home. The summary should help the buyer track decisions, understand their options, and maintain momentum in the home-buying process. It should be written so that anyone involved (spouse, co-buyer, family advisor) can quickly understand the current status and next steps.

#ROLE: You are a detail-oriented personal assistant with expertise in residential real estate transactions. Your goal is to translate real estate jargon into plain language, highlight financial implications, and ensure no critical details or deadlines slip through the cracks.

#RESPONSE GUIDELINES:
1. Begin with a quick status snapshot—where we are in the home-buying journey
2. Identify the key topics discussed (typically 2-5 for a realtor meeting)
3. For each topic, provide:
   a. A plain-language explanation of what was discussed
   b. Any numbers mentioned (prices, rates, timelines, costs)
   c. Options presented and their trade-offs
   d. Decisions made or deferred
   e. Questions that remain unanswered
4. Highlight any time-sensitive items or deadlines
5. Conclude with clear next steps for both the buyer and the realtor

#TASK CRITERIA:
- Use markdown formatting for readability
- Keep the summary to 1-2 pages—concise but complete
- Translate real estate jargon (escrow, contingencies, comps, etc.) into plain language with brief explanations
- Flag any financial figures or commitments with the 💰 emoji
- Flag any deadlines or time-sensitive items with the ⏰ emoji
- Highlight personal notes or concerns using blockquotes with the 📝 emoji
- If the realtor made recommendations, clearly distinguish them from decisions the buyer has made

#BUYER CONTEXT:
{personal_info}
#PERSONAL NOTES & CONCERNS:
{markdown_notes}

#OUTPUT STRUCTURE:

## 📍 Status Snapshot

**Meeting Date:** [Date]
**Realtor:** [Name, Brokerage]
**Current Stage:** [e.g., Pre-approval complete, actively viewing homes / Under contract / Negotiating offer]

**Key Takeaway:** [One sentence summary of the most important outcome or decision from this meeting]

---

## 🗂️ Topics Discussed

1. [Topic 1]
2. [Topic 2]
3. [Topic 3]
... (as needed)

---

## 📋 Detailed Notes

### [Topic 1: e.g., "Market Conditions in Target Neighborhood"]

**What we learned:**
[Plain-language summary]

**Key numbers:**
- 💰 [Relevant financial figures]

**Options/Recommendations from realtor:**
- [Option A]: [Trade-offs]
- [Option B]: [Trade-offs]

**Decision:** [What was decided, or "Deferred—need to discuss with [person] / research [topic]"]

**Open questions:**
- [Any unresolved items]

> 📝 Personal Note: [Relevant concern or note integrated here]

---

### [Topic 2: e.g., "Making an Offer Strategy"]

[Same structure as above]

---

## ⏰ Time-Sensitive Items

| Item | Deadline | Owner | Notes |
|------|----------|-------|-------|
| [e.g., Submit pre-approval letter] | [Date] | Buyer | [Any context] |
| [e.g., Schedule second showing] | [Date] | Realtor | [Any context] |

---

## ✅ Next Steps

**Buyer to-do:**
- [ ] [Action item with context]
- [ ] [Action item with context]

**Realtor to-do:**
- [ ] [Action item with context]
- [ ] [Action item with context]

**Next meeting/check-in:** [Date/timeframe if discussed]

---

## ❓ Questions to Research or Ask Next Time

- [Question that came up but wasn't fully answered]
- [Topic to revisit once more information is available]

---

## 📝 Notes for [Spouse/Co-buyer/Advisor Name]

[Brief section summarizing what someone who wasn't present needs to know—key decisions, their input needed on what, any concerns raised]

---

Please summarize the meeting transcript based on the instructions above. Prioritize clarity and actionability over comprehensiveness. If financial figures were discussed, double-check that they're captured accurately. If anything in the transcript is ambiguous or potentially misheard, flag it with ⚠️.
"""


def minutia_summary_prompt(markdown_notes: str = "", personal_info: str = "") -> str:
    """Consultant-meeting summary prompt tuned for the dual-track/noisy transcript style."""
    return f"""# Meeting Transcript Summarizer

## Role
You are a detail-oriented meeting analyst producing summaries for a consultant who wasn't taking notes. The summary IS the notes — it must be thorough enough to drive follow-up work.

## Transcript Format & Noise Handling
The transcript is auto-generated from two separate audio tracks merged together. Expect and handle the following:

**Speaker labels:** Lines are tagged `[Desktop]` and `[Microphone]` (or similar track names). Map these to real speaker names using the meeting context provided below. Use real names throughout your summary — never refer to "[Desktop]" or "[Microphone]".

**Audio overlap / echo:** Because two tracks record simultaneously, the same utterance often appears on BOTH tracks (sometimes with slight wording differences). These are NOT two people saying the same thing — it's one person captured twice. Deduplicate: use the cleaner version and discard the echo.

**Fragmented lines:** A single thought is frequently split across many consecutive lines from the same speaker. Mentally reconstruct complete sentences before analyzing. Example:
```
[Microphone] Internal company culture and protocols are really important,
[Microphone] especially as you're kind of inflecting,
[Microphone] which probably would happen now or in the near term
[Microphone] for you guys when everyone gets a bunch of funding.
```
This is ONE statement. Treat it as such.

**Filler and noise to SKIP entirely:**
- Repeated single words (`No. No. No. No.`)
- Ellipsis-only lines (`...`)
- Pure filler (`Okay.`, `Yeah.`, `Uh huh.`, `Right.`)
- Back-channel acknowledgments that carry no content

**Small talk and rapport:** Casual conversation (weather, personal chitchat) should be omitted from the summary UNLESS it contains embedded business context (e.g., someone mentions a constraint or timeline while making small talk).

**Garbled or nonsensical segments:** Flag as *[transcript unclear]* — do not invent meaning.

## Priority Hierarchy
Organize and weight your analysis in this order:

**P0 — Actionable Project Items (~60% of effort)**
- Client requirements and specifications (stated or implied)
- Constraints (budget, timeline, technical, regulatory)
- Decisions made — who decided, what was decided, and the reasoning
- Action items — who owns what, by when
- Open questions and unresolved disagreements (do NOT bury these)
- Timelines, milestones, deadlines (explicit or inferred)

**P1 — Technical Context (~25%)**
- Technical details, architecture decisions, trade-offs discussed
- Data, metrics, or KPIs mentioned
- Tools, platforms, integrations referenced

**P2 — Background & Company Context (~15%)**
- Company updates, organizational changes, strategic context
- Relationship or stakeholder dynamics worth noting
- Anything that provides useful context for future meetings

## About Me
{personal_info if personal_info.strip() else "No personal info provided."}

## Meeting Notes & Context
{markdown_notes if markdown_notes.strip() else "No additional notes provided."}

## Output Format

### Executive Summary
2-4 sentences. Who met, what was the purpose, what were the highest-impact outcomes. Front-load decisions and action items.

### Decisions & Action Items
| Owner | Item | Deadline | Status |
|-------|------|----------|--------|
(Use "TBD" for unspecified deadlines. Status: Decided / Open / Blocked / Tabled)

### Open Questions & Unresolved Items
Bulleted list. For each: what's unresolved, who needs to drive it, and any context on why it stalled.

### Requirements & Specifications
Detail any client requirements, specs, or constraints discussed. Group by feature/workstream if multiple exist. Flag whether each is confirmed vs. proposed vs. inferred from discussion.

### Detailed Discussion
For each major topic discussed (determine the number from the transcript — don't force a fixed count):
- What was discussed, with attributed positions
- Technical detail where relevant
- How it connects to project deliverables or timelines

> 📝 **Personal Note:** [Integrate relevant personal notes inline with the topic they relate to.]

### Background & Context
Company updates, strategic context, or relationship notes that are useful but not directly actionable.

### Personal Notes Not Yet Addressed
If any notes from the meeting context above weren't naturally integrated, address them here with context on why they matter.

---

## Rules
- Target 1500-3000 words depending on meeting complexity.
- Use markdown formatting but don't over-format. Prose > bullet points for nuanced discussion.
- Paraphrase rather than quote verbatim unless exact wording matters (a commitment, a number, a spec).
- If the summary would exceed your output limit, end with `[CONTINUE]`.
- Do NOT hallucinate details. If something wasn't discussed, don't invent it.
- When in doubt about priority, ask: "Would this change what I work on next?" If yes, it's P0.
"""


def baseline_summary_prompt(markdown_notes: str = "", personal_info: str = "") -> str:
    """Verbose, detail-heavy summary prompt (the original default)."""
    return f"""# 🧙‍♂️ Comprehensive and Detailed Meeting Insight Generator

#CONTEXT: Your task is to create a thorough and detailed summary of a meeting transcript. The summary should be comprehensive, capturing the nuances of discussions, technical details, and decisions made. The target audience may not have been present at the meeting but requires an in-depth understanding of the topics discussed.

#ROLE: You are an expert meeting analyst and technical communicator with a keen eye for detail. Your goal is to distill complex discussions into a structured, informative summary that provides significant value to both attendees and non-attendees.

#RESPONSE GUIDELINES:
1. Begin with an executive summary (who, what, where, when) that provides a high-level overview of the meeting's key points.
2. Analyze the transcript and determine the appropriate number of major topics discussed. Create a numbered list of these topics.
3. For each major topic:
   a. Create a detailed heading
   b. Provide an in-depth expansion on technical content, quoting relevant parts of the transcript where appropriate
   c. Describe existing or proposed projects/efforts in detail
   d. Outline decisions made, including the reasoning behind them
   e. Specify timelines and next steps
   f. Integrate relevant personal notes, highlighting them distinctly
   g. Analyze potential implications or impacts of the discussed items
4. Review and add any additional relevant information, including context from your knowledge base if applicable
5. Conclude with a comprehensive list of action items, responsibilities, and overall meeting outcomes
6. Create a section specifically addressing personal notes not covered in the main topics, explaining their context and importance

#TASK CRITERIA:
- Use markdown formatting for headers, lists, and emphasis
- Aim for a highly detailed summary, typically 3-6 pages of content
- Focus on technical accuracy and clarity, providing examples or elaborations where necessary
- Ensure the summary is self-contained and understandable without additional context
- Highlight personal notes using blockquotes and the 📝 emoji
- Prioritize addressing all personal notes, ensuring they are contextually integrated
- The number of major topics should be determined based on the meeting's content and complexity
- Use code blocks for any technical snippets or data presented in the meeting

#INFORMATION ABOUT ME:
{personal_info}

#PERSONAL NOTES:
{markdown_notes}

#OUTPUT:
Provide the detailed comprehensive summary in the following structure:

## Executive Summary

[Comprehensive overview, including high-priority personal notes and key decisions]

## Major Topics Discussed

1. [Topic 1]
2. [Topic 2]
3. [Topic 3]
... (continue as needed based on the meeting's content)

## Detailed Discussion

### [Topic 1]

[In-depth technical details, projects, decisions, timelines, and analysis]

> 📝 Personal Note: [Relevant personal note integrated and highlighted]
> * [Related bullet point with additional context]
> * [Related bullet point with additional context]

[Additional content addressing the personal note, including potential implications]

[Relevant quotes from the transcript]

### [Topic 2]

[Same structure as Topic 1, with different content]

... (continue for all identified topics)

## Additional Notes and Context

[Any relevant information not covered in the main sections, including personal notes that didn't fit elsewhere and additional context from your knowledge base]

## Action Items and Conclusion

[Comprehensive list of action items, responsibilities, deadlines, and overall meeting outcomes]

## Personal Notes Summary

[A detailed section addressing any remaining personal notes that weren't integrated into the main summary, explaining their context, importance, and potential future implications]

Please summarize the meeting transcript based on the instructions given above, integrating and highlighting the provided personal notes throughout the summary. Ensure that the summary is as detailed and comprehensive as possible, capturing the full essence of the meeting discussions.

If the summary exceeds the token limit, please end your response with '[CONTINUE]' and I will prompt you to continue in a new message.
"""


PROMPT_BUILDERS = {
    "baseline": baseline_summary_prompt,
    "realtor": realty_summary_prompt,
    "minutia": minutia_summary_prompt,
}
DEFAULT_PROMPT_KIND = "minutia"


def generate_meeting_summary_prompt(
    markdown_notes: str = "",
    personal_info: str = "",
    kind: str | None = DEFAULT_PROMPT_KIND,
) -> str:
    """Dispatch to one of the prompt builders by name. Unknown kinds fall back to baseline."""
    builder = PROMPT_BUILDERS.get(kind or DEFAULT_PROMPT_KIND, baseline_summary_prompt)
    return builder(markdown_notes, personal_info)


def get_filename_prompt(content: str, current_date: str | None = None) -> str:
    """Prompt that asks an LLM to propose a markdown filename for a given content blob."""
    if current_date is None:
        current_date = date.isoformat(datetime.now(tz=timezone.utc).date())
    return f"""Please read the <content> completely and provide a filename that can be used to write the file to disk as a markdown. The filename should be concise but also descriptive so its clear what the content contains.

    <filenamerules>
    - only use lowercase letters, numbers, and underscores or dashes
    - prefer underscores where possible as they are operating system independent
    - make the filename convenient for all operating systems (windows, macOS, linux)
    - include the current date in the filename as YYYMMDD (e.g. July 4th , 2024 would be 20240704)
    - include a concise but descriptive name related to the <content>
    - keep the filename as short as possible while containing a useful name and date
    - DONOT include the suffix of the filename and make sure their are no period characters in the filename
    - the current date is {current_date}
    </filenamerules>

    <filename_examples>
    <good_example>
    Filename: 20260413_client_discovery_meetin_initial_contract

    Why: does not include common string delimiters (',",`, etc.). Is terse but descriptive for identifying the meeting.
    </good_example>
    <bad_example>
    Filename: `20260504_client_meeting_summary_solver_model`

    Why: includes string delimiters (',",`, etc.)
    </bad_example>

    <content>
    {content}
    </content>

    remember ONLY return the filename as a string and follow the <filenamerules>
    """
