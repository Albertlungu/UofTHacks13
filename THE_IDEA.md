# Project Idea
**shadow**

- Using Logitech cams and Airpods (audio I/O)
- AI companion
- Proof of concept for projection
- Also uses 11Labs to make voice
- Amplitude takes what the user said, stores it (as memories), and creates an analysis that is then sent to Gemini, which uses that as a boilerplate for generating responses.
- As the user walks around, the cameras see them, and follow them, tracking the user. 
    - The cameras are stationed on stepper motors so that they can rotate and follow the user.
- As they walk, they can talk, as they talk to themselves, but the audio is being captured by Airpods, which will be configured to use Gemini API or some other model.
- The audio is then put through Whisper and turned into text.
- The user's first couple of sentences will be sent into a specifically designed "emotion model", made to interpret emotion, which will then output a style in which Gemini will have to respond.
- Gemini will slowly adapt to the user's personality, and will eventually become very similar to the user, being able to help them with ideas.
- This means that when the user offers an idea, based on their personality, Gemini will either support, reject, or offer counter-ideas.
- The camera analyzes the user's face, determining their expression, sending it to Gemini, which will then act accordingly.
- The companion's projection will be displayed on a MacBook
- The cameras are on a sort of plate that has a large radius to replicate "rails" to be able to follow the users in a straight line (and not in a circle)
