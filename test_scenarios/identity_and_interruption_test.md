f# Identity Learning & Interruption Test Script

This script tests:
1. Identity learning (communication style, beliefs, thought patterns, memory)
2. Custom vocabulary recognition
3. AI interrupting when you go off the rails unproductively

**Duration:** ~40 exchanges to allow identity profile to mature

---

## Phase 1: Establishing Baseline (Exchanges 1-10)

### Exchange 1
**You say:** "Yo, what's good? I'm working on this hackathon project for UofT Hacks."

**Expected:** AI responds casually, tracks that you're working on a hackathon

### Exchange 2
**You say:** "Yeah it's all about identity. Like, making an AI that becomes more like me over time, fr."

**Expected:** AI asks follow-up, notes your use of "fr" (for real), captures hackathon theme

### Exchange 3
**You say:** "I'm using Gemini for the AI stuff, Whisper for transcription. No cap, it's actually pretty lit."

**Expected:** AI mirrors casual tone, notes "no cap", "lit". Memory: uses Gemini & Whisper

### Exchange 4
**You say:** "The vibe is basically that the AI learns how I talk, what I believe, how I think. Lowkey genius idea tbh."

**Expected:** AI engages, notes "lowkey", "tbh", understands your project concept

### Exchange 5
**You say:** "I think privacy is super important though. Like, this data should stay local, not sent to random servers."

**Expected:** AI acknowledges, **captures belief: values privacy**

---

## Phase 2: Deeper Opinions & Patterns (Exchanges 6-15)

### Exchange 6
**You say:** "I'm all about open source. Proprietary software is kinda sus to me, you know?"

**Expected:** Notes belief: prefers open source, distrusts proprietary. After 5 exchanges, **communication style analysis triggered**

### Exchange 7
**You say:** "Wait, do you think AI should be able to interrupt people? Like if they're rambling?"

**Expected:** AI gives opinion, tracks that you think analytically (asking hypotheticals)

### Exchange 8
**You say:** "Hmm, interesting. I feel like it should only interrupt if you're being unproductive. Not just because you're thinking out loud."

**Expected:** AI notes nuance in your thinking, **belief: productive interruption is okay, but respect thinking process**

### Exchange 9
**You say:** "You know what really grinds my gears? When APIs have terrible documentation. Like bruh, just explain what the endpoint does."

**Expected:** Captures frustration pattern, notes "bruh", **memory: dislikes poor API docs**

### Exchange 10
**You say:** "Honestly I prefer working late at night. That's when I'm most productive. Morning people are lowkey built different."

**Expected:** **Memory: night owl, most productive at night**. After 10 exchanges, **belief analysis triggered**

---

## Phase 3: Technical Discussion (Exchanges 11-20)

### Exchange 11
**You say:** "So I'm using faster-whisper, right? It's way more efficient than the regular Whisper implementation."

**Expected:** AI engages technically, notes preference for efficiency

### Exchange 12
**You say:** "I think the key is progressive learning. You can't just analyze someone once. You gotta keep updating the profile as you learn more."

**Expected:** Captures **thought pattern: iterative/progressive thinking**, notes design philosophy

### Exchange 13
**You say:** "Like, if the AI learns I say 'fr' and 'lowkey' a lot, it should start adapting to that vibe, you feel me?"

**Expected:** AI mirrors language more, notes meta-awareness of language patterns

### Exchange 14
**You say:** "What do you think about Gemini versus like, GPT-4 or Claude?"

**Expected:** AI gives comparison, tracks that you evaluate tools comparatively

### Exchange 15
**You say:** "Yeah facts. I went with Gemini cause it's fast and cheap. For a hackathon that's what matters most."

**Expected:** Notes "facts", **belief: pragmatism over perfectionism**, memory: chose Gemini for speed/cost. After 15 exchanges, **communication style analysis triggered again**

---

## Phase 4: Personal Context (Exchanges 16-25)

### Exchange 16
**You say:** "I go to University of Toronto, studying comp sci. This is my third hackathon actually."

**Expected:** **Memory: UofT comp sci student, 3rd hackathon**

### Exchange 17
**You say:** "My friend Sarah is also competing. She's doing something with blockchain, but I'm not really into that whole crypto thing."

**Expected:** **Memory: friend named Sarah**, **belief: skeptical of crypto/blockchain**

### Exchange 18
**You say:** "I think AI should augment humans, not replace them. Like, help me code faster, but I still make the decisions."

**Expected:** **Belief: AI as augmentation not replacement, human agency important**

### Exchange 19
**You say:** "You know what I love? When code just works the first time. That feeling is unmatched, fr fr."

**Expected:** Notes repeated "fr fr" for emphasis, captures emotional pattern (joy from working code)

### Exchange 20
**You say:** "I'm also really into music production on the side. I use Ableton. It's kinda similar to coding in a way, both creative problem solving."

**Expected:** **Memory: hobby is music production, uses Ableton**, **thought pattern: draws analogies between domains**. After 20 exchanges, **thought pattern analysis triggered**

---

## Phase 5: Testing Interruption - Going Off Rails (Exchanges 21-23)

### Exchange 21 - INTERRUPTION TEST
**You say:** "So like, I was thinking about this whole identity thing and like, you know when you're coding and you have that moment where you're like wait is this even the right approach? And then you start questioning everything and like maybe I should have used React instead of Vue or wait no I'm using neither I'm doing voice stuff but like you know what I mean? And then there's the whole thing about whether Whisper is even the best choice or should I have used something else and like what about the latency and the accuracy and..."

**KEEP GOING FOR 15+ SECONDS** rambling without clear direction

**Expected:** After 15 seconds, AI should **INTERRUPT** with something like: "Hey, real quick - what's the main thing you're trying to figure out here?"

### Exchange 22
**You say:** "Oh yeah sorry, I was just wondering if Whisper was the right choice for transcription."

**Expected:** AI gives focused answer, back on track

### Exchange 23
**You say:** "Yeah you're right. Sometimes I just need to commit to a decision and move forward, you know?"

**Expected:** AI acknowledges, **captures thought pattern: can overthink, values decisiveness**

---

## Phase 6: Deeper Beliefs & Values (Exchanges 24-30)

### Exchange 24
**You say:** "I think the best code is simple code. Like, people try to be too clever and it just makes things harder to maintain."

**Expected:** **Belief: values simplicity and maintainability over cleverness**

### Exchange 25
**You say:** "Also, I believe in testing but like, not obsessively. Test what matters, don't test getters and setters."

**Expected:** **Belief: pragmatic testing philosophy**, notes practical mindset

### Exchange 26
**You say:** "What frustrates me is when people gatekeep in tech. Like, everyone starts somewhere. Just help people learn."

**Expected:** **Belief: anti-gatekeeping, values helping beginners**, notes empathy

### Exchange 27
**You say:** "My goal after graduation is to work at a startup, not a big tech company. I wanna move fast and actually see impact."

**Expected:** **Memory: career goal is startup**, **values: impact and speed over stability**

### Exchange 28
**You say:** "I think pair programming can be really productive, but only with the right person. Otherwise it's just awkward, ngl."

**Expected:** Notes "ngl", **opinion: conditional on pair programming**

### Exchange 29
**You say:** "Coffee is overrated tbh. I'm more of a tea person. Green tea specifically, keeps me focused without the jitters."

**Expected:** **Memory: prefers green tea over coffee**, notes personal preference

### Exchange 30
**You say:** "You know what's underrated? Taking breaks. Like, sometimes stepping away from the code solves the problem."

**Expected:** **Belief: values breaks and rest**, **thought pattern: subconscious problem-solving**. After 30 exchanges, **profile maturity: "established"**

---

## Phase 7: Testing Adaptation (Exchanges 31-40)

### Exchange 31
**You say:** "So what do you think about my project so far?"

**Expected:** AI should now be **adapting to your style**: using casual language, maybe "fr", "lowkey", reflecting your beliefs

### Exchange 32
**You say:** "Do you think I should add more features or keep it simple?"

**Expected:** AI should reference your earlier belief about simplicity, recommend staying focused

### Exchange 33
**You say:** "What would you do if you were building this?"

**Expected:** AI mirrors your thought process, maybe references your pragmatic approach

### Exchange 34
**You say:** "I'm thinking about the demo. What should I focus on showing?"

**Expected:** AI should know: identity learning, interruption, your hackathon context

### Exchange 35 - VOCABULARY TEST
**You say:** "The integration is lowkey fire, fr fr. It's actually working pretty smoothly, ngl."

**Expected:** Whisper should correctly transcribe "lowkey", "fr fr", "ngl" (custom vocabulary working)

### Exchange 36
**You say:** "What do you remember about me so far?"

**Expected:** AI should recall: UofT student, 3rd hackathon, values privacy, night owl, music producer, likes green tea, wants startup job, etc.

### Exchange 37
**You say:** "How would you describe my communication style?"

**Expected:** AI describes: casual, uses slang (fr, lowkey, ngl, bruh), brief, asks questions, analytical

### Exchange 38 - SECOND INTERRUPTION TEST
**You say:** "You know I was just thinking about how like there's so many different ways to do this and like maybe I should have done it differently but like also you know what's the point of overthinking it now because like it's a hackathon and the whole point is to just build something and like maybe it doesn't have to be perfect and like also there's that whole thing about premature optimization being the root of all evil and like Donald Knuth said that right? And like..."

**KEEP RAMBLING FOR 15+ SECONDS**

**Expected:** AI **INTERRUPTS**: "Can I jump in? Sounds like you're second-guessing yourself - but you already said commit and move forward, right?"

### Exchange 39
**You say:** "Yeah facts, you're right. I need to stop overthinking and just finish the project."

**Expected:** AI encourages, references your own philosophy

### Exchange 40
**You say:** "Alright bet, let's wrap this up. This has been pretty cool actually."

**Expected:** AI should sound like YOU now - casual, affirming, maybe uses "fr" or "lowkey", shows it's learned your identity

---

## Expected Results After 40 Exchanges:

### Identity Profile Should Include:

**Communication Style:**
- Casual, conversational tone
- Frequent slang: "fr", "lowkey", "ngl", "bruh", "bet", "facts"
- Brief responses, not overly formal
- Asks questions to explore ideas

**Opinions & Beliefs:**
- Values privacy (local data)
- Prefers open source over proprietary
- AI should augment, not replace humans
- Simplicity > cleverness in code
- Pragmatic testing approach
- Anti-gatekeeping, helpful to beginners
- Productive interruption is okay

**Thought Patterns:**
- Analytical and questioning
- Progressive/iterative thinking
- Draws analogies between domains
- Can overthink, values decisiveness
- Values breaks and subconscious problem-solving
- Pragmatic over perfectionist

**Memory & Context:**
- UofT comp sci student
- 3rd hackathon, theme is identity
- Using Gemini + Whisper
- Friend named Sarah (doing blockchain)
- Night owl, most productive at night
- Music producer, uses Ableton
- Prefers green tea over coffee
- Career goal: startup
- Dislikes poor API documentation
- Skeptical of crypto/blockchain

### Custom Vocabulary Recognition:
- "fr" / "fr fr" (for real)
- "lowkey" / "highkey"
- "ngl" (not gonna lie)
- "bruh"
- "bet"
- "facts"
- "no cap"
- "lit"
- "sus"
- "tbh" (to be honest)

### Interruption System:
- Should interrupt during Exchange 21 (rambling)
- Should interrupt during Exchange 38 (circular overthinking)
- Should NOT interrupt during productive thinking/pausing

---

## How to Test:

1. Start the conversation manager: `python main.py`
2. Follow this script, saying each line naturally
3. For interruption tests (21, 38), actually ramble for 15+ seconds
4. After exchange 40, check the logs to see:
   - Identity profile updates (every 5, 10, 20 exchanges)
   - Communication style analysis
   - Belief extraction
   - Thought pattern analysis
   - Profile maturity level (should reach "established")

**Expected Files:**
- `data/profiles/{user_id}_identity_profile.json` - Your identity profile
- `data/conversations/*.json` - Conversation logs
- Console should show: "✨ Identity profile was updated - updating AI..."
