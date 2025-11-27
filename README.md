# Scanly

A modern application designed to analyze and improve your resume using cutting-edge techniques.

## Key Features & Benefits

- **Resume Analysis:** Upload your resume and receive a comprehensive score based on ATS compatibility, tone, content, and structure.
- **ATS (Applicant Tracking System) Optimization:** Get specific tips to improve your resume's compatibility with ATS software.
- **Detailed Feedback:**  Understand your resume's strengths and weaknesses with a breakdown of scores in key areas.
- **Resume Examples:** Compare your resume to sample resumes to identify areas for improvement.
- **Dockerized Deployment:** Easy to deploy and run using Docker.
- **Modern UI:** Built with React, TypeScript, and TailwindCSS for a responsive and user-friendly experience.

## Prerequisites & Dependencies

Before you begin, ensure you have the following installed:

- **Node.js:** (version 20 or higher)
- **npm:** (Node Package Manager - comes with Node.js)
- **Docker:** (for containerized deployment)

## Installation & Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone git@github.com:christianh-9/scanly.git
   cd scanly
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Run in Development Mode (without Docker):**

   ```bash
   npm run start
   ```

   This will start the development server and open the application in your browser.

4. **Build and Run with Docker:**

   ```bash
   docker build -t scanly .
   docker run -p 3000:3000 scanly
   ```

   This will build the Docker image and run the application in a container, accessible at `http://localhost:3000`.

## Usage Examples

1. **Uploading a Resume:**

   - Navigate to the main page.
   - Use the "File Uploader" component to upload your resume in PDF format.
   - The application will process the resume and display the analysis results.

2. **Viewing Analysis Results:**

   - The analysis results are displayed in several sections:
      - **Overall Score:** A general score representing the quality of your resume.
      - **ATS Score:** Indicates how well your resume will perform in Applicant Tracking Systems.
      - **Tone and Style, Content, Structure:** Scores and tips related to these specific aspects of your resume.

3. **Comparing with Example Resumes:**
   -  The application provides several sample resumes for comparison. Analyze these resumes to get insights into effective resume writing.

## Configuration Options

The application can be configured through environment variables.  While the provided `Dockerfile` doesn't explicitly use environment variables for customization, you could modify the `Dockerfile` or the application's code to incorporate environment variables if needed.  Example:

   In `Dockerfile`, add:
   ```dockerfile
   ENV PORT=3000
   ```
   And in your node application:
   ```typescript
   const port = process.env.PORT || 3000;
   ```

## Contributing Guidelines

Contributions are welcome! If you'd like to contribute to this project, please follow these guidelines:

1. **Fork the repository.**
2. **Create a new branch for your feature or bug fix.**
3. **Implement your changes.**
4. **Write tests for your code.**
5. **Submit a pull request.**

Please ensure that your pull request includes:

- A clear description of the changes.
- Test cases that cover the changes.
- Updated documentation if necessary.

## License Information

This project has no specified license. All rights are reserved by the owner, christianh-9.

## Acknowledgments

- This project utilizes the `pdfjs-dist` library for PDF parsing and rendering.
- The UI is styled using TailwindCSS.
