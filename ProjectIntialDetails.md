# Problem Statement and Target Users:
Scam messages have become increasingly common through SMS, email, messaging applications, and social media platforms. Many users find it difficult to distinguish legitimate messages from fraudulent ones, which can lead to financial losses, identity theft, and exposure of personal information.

The proposed application, Scam Message Risk Detector, aims to help users identify potentially fraudulent messages by using AI to analyze message content and assess the likelihood that a message is a scam.

The intended users are:

- General smartphone and internet users
- Students
- Elderly individuals
- Small business owners
- Anyone who receives suspicious digital messages

# User Input:
Text message (include phone number)

# Use of AI:
The AI component will analyze the submitted message and identify characteristics commonly associated with scams, such as:

suspiscious links
spelling errors
urgency levels
too informal
incentives

The AI is the core engine of the application because every message must be analyzed by AI before a decision can be made.

## AI Output:
The AI will provide:

Scam probability score
Scam category
Risk level
Detected scam indicators
Explanation of why the message is suspicious

# Business Rules:
Categorise the scam message based on High, Medium and Low risk.

## Input validation rules
Message content cannot be empty.
Include phone number (check country code using AI) with text message