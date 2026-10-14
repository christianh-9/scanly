// A real review produced by Scanly's backend (Gemini Flash-Lite) for a fictional sample resume.
// Shown at /demo so visitors can see the product without signing in; it never calls Gemini or Puter.
export const DEMO_JOB_TITLE = "Software Engineer";
export const DEMO_JOB_DESCRIPTION =
  "We are hiring a software engineer to build web applications with React, TypeScript and Python. " +
  "You will design APIs, write tests, and work with product and design to ship features.";

export const DEMO_RESUME: Resume = {
  id: "demo",
  companyName: "Sample review",
  jobTitle: DEMO_JOB_TITLE,
  imagePath: "/demo/resume.png",
  resumePath: "/demo/resume.pdf",
  feedback: {
    "overallScore": 68,
    "ATS": {
      "score": 75,
      "tips": [
        {
          "type": "good",
          "tip": "Included standard contact information."
        },
        {
          "type": "good",
          "tip": "Listed relevant tech stack keywords."
        },
        {
          "type": "improve",
          "tip": "Add TypeScript to skills section."
        }
      ]
    },
    "toneAndStyle": {
      "score": 70,
      "tips": [
        {
          "type": "good",
          "tip": "Clean and concise layout.",
          "explanation": "The formatting is straightforward and easy to read quickly."
        },
        {
          "type": "improve",
          "tip": "Strengthen action verbs in bullets.",
          "explanation": "Use stronger verbs like engineered instead of built."
        },
        {
          "type": "improve",
          "tip": "Include more technical metrics.",
          "explanation": "Quantify API performance or user scale to show impact."
        }
      ]
    },
    "content": {
      "score": 65,
      "tips": [
        {
          "type": "good",
          "tip": "Highlighted a relevant coding bootcamp.",
          "explanation": "Shows foundational transition into software engineering."
        },
        {
          "type": "improve",
          "tip": "Address missing TypeScript experience.",
          "explanation": "The job requires TypeScript which is absent from the resume."
        },
        {
          "type": "improve",
          "tip": "Add details about testing and APIs.",
          "explanation": "Mention specific testing frameworks and API design work."
        }
      ]
    },
    "structure": {
      "score": 75,
      "tips": [
        {
          "type": "good",
          "tip": "Clear chronological ordering",
          "explanation": "The resume follows a standard reverse-chronological order, making it easy for recruiters to scan."
        },
        {
          "type": "improve",
          "tip": "Add a professional summary",
          "explanation": "Expand the summary to highlight your unique background in education and software engineering."
        },
        {
          "type": "improve",
          "tip": "Incorporate a dedicated achievements section",
          "explanation": "Quantify your teaching and development achievements more prominently in a dedicated section."
        }
      ]
    },
    "skills": {
      "score": 70,
      "tips": [
        {
          "type": "good",
          "tip": "Relevant technical stack listed",
          "explanation": "Core technologies like JavaScript, React, and Node.js are clearly displayed."
        },
        {
          "type": "improve",
          "tip": "Add missing required skills",
          "explanation": "Include TypeScript and Python as mentioned in the job description."
        },
        {
          "type": "improve",
          "tip": "Group skills by category",
          "explanation": "Organize skills into categories like languages, frameworks, and tools for better readability."
        }
      ]
    }
  },
};
