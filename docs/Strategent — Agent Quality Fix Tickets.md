# **Strategent — Agent Quality Fix Tickets**

## **Ticket 1: Platform selection is too generic for the audience**

**Priority:** High  
**Owner:** AI / Backend

### **Issue**

The agent currently chooses a platform that looks plausible, but the choice is not strongly grounded in the user brief. For example, when the audience is students and the goal is signups, the agent still defaults to LinkedIn without a strong strategic justification.

### **Root Cause**

The current decision logic depends too heavily on a single LLM response and does not use a structured platform-fit scoring layer. Audience, goal, content type, and platform behavior are not being weighted explicitly.

### **Fix**

Add a platform selection layer that scores each platform using explicit factors such as:

* audience fit  
* goal fit  
* content format fit  
* tone fit  
* expected conversion fit

The LLM should explain the result, but the platform should first be chosen by structured logic or weighted scoring.

### **Acceptance Criteria**

* The agent explains why the chosen platform is best for the given audience and goal.  
* The response includes a clear comparison against at least one alternative platform.  
* The platform choice changes when the audience changes.  
* The selection no longer feels like a generic default.

---

## **Ticket 2: Content generation is not aligned with the actual business goal**

**Priority:** High  
**Owner:** AI / Backend

### **Issue**

The generated content is polished, but it is often awareness-focused instead of being tightly aligned with the stated goal, such as increasing signups.

### **Root Cause**

The generation prompt focuses too much on topic and tone, and not enough on conversion objective. The model is writing “good content” instead of “content that drives the requested action.”

### **Fix**

Update the generation prompt and logic so the content explicitly optimizes for:

* the business goal  
* the target audience  
* the platform choice  
* the call to action

The output should always include:

* hook  
* body  
* CTA  
* optional hashtags  
* conversion intent

### **Acceptance Criteria**

* Generated content directly supports the goal stated in the brief.  
* If the goal is signups, the copy pushes users toward signup.  
* The content style changes based on platform.  
* The output does not feel like a generic thought-leadership post.

---

## **Ticket 3: Performance simulation numbers feel arbitrary**

**Priority:** High  
**Owner:** AI / Backend

### **Issue**

The simulation output gives performance values, but the numbers do not look explainable enough. The judge may ask why a platform scored a certain way, and the agent does not yet show enough reasoning behind the values.

### **Root Cause**

The simulation layer is producing values without exposing the logic used to derive them. The output looks visual and polished, but not sufficiently evidence-driven.

### **Fix**

Introduce a scoring explanation layer for simulation. The output should include:

* platform fit score  
* audience alignment score  
* goal alignment score  
* format suitability score  
* reasoning summary

The model should not only produce a number; it should explain what contributed to that number.

### **Acceptance Criteria**

* Each simulated score has a visible explanation.  
* The alternative platform score is justified.  
* The simulation can explain why one platform performs better than another.  
* The numbers feel derived from logic, not decoration.

---

## **Ticket 4: Feedback loop exists, but it does not visibly change strategy**

**Priority:** High  
**Owner:** AI / Backend

### **Issue**

The feedback section shows predicted vs actual performance and a learning note, but the system does not clearly demonstrate that it learned from the previous result.

### **Root Cause**

The feedback output is currently informational, not adaptive. There is no persistent strategy update or visible carryover into the next decision.

### **Fix**

Store the last strategy result and use it in the next run. The next recommendation should explicitly respond to the previous outcome.

Example:

* If LinkedIn underperforms for students, the next run should shift to a better-fitting channel and explain why.

### **Acceptance Criteria**

* The next recommendation changes based on prior results.  
* The learning note references the actual performance gap.  
* The dashboard shows that the agent improved its strategy from feedback.  
* The system behaves like it is learning, not just reporting.

---

## **Ticket 5: The reasoning chain is not visible enough in the UI**

**Priority:** Medium  
**Owner:** Frontend / AI

### **Issue**

The UI looks clean, but the actual reasoning flow is not visible enough. The output feels like a finished result rather than an agent thinking through a decision.

### **Root Cause**

The UI presents the final answer well, but the intermediate reasoning stages are not emphasized enough. The agent’s thought process is hidden.

### **Fix**

Make the flow explicit in the UI:

1. Brief analysis  
2. Platform scoring  
3. Decision  
4. Simulation  
5. Content generation  
6. Feedback / learning

Use separate cards or clearly labeled stages so the judge can follow the agent logic step by step.

### **Acceptance Criteria**

* The judge can understand the full flow in one glance.  
* The reasoning is visible, not implied.  
* The UI feels like an agent dashboard, not a content editor.  
* Each step has a distinct purpose and visible output.

---

# **Final Quality Target**

The prototype should feel like an **AI strategist**, not a **content wrapper**.

### **The system is ready when it can:**

* choose a platform for a specific audience with a clear reason,  
* generate content that supports the actual business goal,  
* simulate outcome with explainable scoring,  
* update its next recommendation after feedback,  
* and show the full reasoning chain in the UI.