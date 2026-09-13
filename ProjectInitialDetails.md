# Project Initial Details Submission

**Project Title:** Scam Message Risk Detector

**Domain**: Safety, Risk and Compliance (Scam and Fraud Prevention)

**Repository URL:** https://github.com/Jon1oh/DevOps-Team-6

## 1. Problem Statement and Target Users

Scam messages have become increasingly common through SMS, email, messaging applications, and social media platforms. Many users find it difficult to distinguish legitimate messages from fraudulent ones, which can lead to financial losses, identity theft, and exposure of personal information.

The proposed application, AI Scam Message Detector, aims to help users identify potentially fraudulent SMS messages by using AI to analyze message content, assess scam risk, explain suspicious indicators, and provide recommendations to help users make informed decisions.

**Target Users:**

- General smartphone and internet users (e.g. students,  adults, elderly)
- Anyone who receives suspicious digital messages

## 2. User Inputs

- The text content of the message the user wants checked.
- The sender's phone number, included alongside the message so the AI can verify the country code and cross-reference it against known scam-sender patterns.

## 3. Use of AI

The AI component will analyze the submitted message and identify characteristics commonly associated with scams, such as:

- Suspicious links
- Spelling errors
- Urgency levels
- Overly informal tone
- Incentives/rewards offered

The AI is the core engine of the application because every message must be analyzed by AI before a decision can be made.

**AI Output:**

Upon analysing the user's messaeg input, the AI will provide:

- Timestamp
- Scam probability score
- Scam category
- Risk level
- Detected scam indicators
- Explanation of why the message is suspicious

## 4. Business Rules

**Input Validation Rules:**

- Message content cannot be empty.
- User input must be in string format.
- The submission must include a phone number (country code checked using AI) alongside the text message.

**Logic Management Rules:**

These are the decisions made from the AI output:

- Categorise the scam message based on High, Medium and Low risk and categories.
- Determine risk level of the scam message
- Generate scam-specific recommendations for users, based on their provided message input.

**Data Management Rules:**
- Store all analyzed messages and output from AI manager in JSON format.
- Records of previously processed user inputs from other process runs to be persistent.
- Generate historical summaries of risk levels and categories of all received messages.
- Load previous scam message records from the JSON file on program start up.

## 5. Programs / API to be used

**Primary AI API:**
- OpenAI API (GPT-4o)

**Alternative AI APIs (Subject to Evaluation):**
- VirusTotal API
- PhishText.Ai