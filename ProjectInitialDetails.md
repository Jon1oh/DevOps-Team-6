# Project Initial Details Submission

**Project Title:** Scam Message Risk Detector

## 1. Problem Statement and Target Users

Scam messages have become increasingly common through SMS, email, messaging applications, and social media platforms. Many users find it difficult to distinguish legitimate messages from fraudulent ones, which can lead to financial losses, identity theft, and exposure of personal information.

The proposed application, Scam Message Risk Detector, aims to help users identify potentially fraudulent messages by using AI to analyze message content and assess the likelihood that a message is a scam.

**Target Users:**

- General smartphone and internet users
- Students
- Elderly individuals
- Small business owners
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

The AI will provide:

- Scam probability score
- Scam category
- Risk level
- Detected scam indicators
- Explanation of why the message is suspicious

## 4. Business Rules

Categorise the scam message based on High, Medium and Low risk.

**Input Validation Rules:**

- Message content cannot be empty.
- The submission must include a phone number (country code checked using AI) alongside the text message.

## Repository Information

**Repository URL:** https://github.com/Jon1oh/DevOps-Team-6
