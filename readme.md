# CodeGenesis

> AI-powered coding platform that generates programming challenges tailored to a user's skill level.

## Overview

CodeGenesis is a modern coding practice platform built with **FastAPI**, **PostgreSQL**, and **Judge0**. Unlike traditional coding platforms with static question banks, CodeGenesis leverages AI to generate coding problems, explanations, hints, and personalized learning experiences.

The goal is to provide an adaptive environment where users can practice coding with dynamically generated challenges and receive instant feedback through an online code execution engine.

---

## Features

### Authentication
- User Registration
- User Login
- JWT Authentication
- Refresh Tokens
- Role-Based Access Control (RBAC)

### AI-Powered Problems
- AI-generated coding questions
- Multiple difficulty levels
- Topic-based question generation
- AI-generated examples and explanations
- AI-generated hints

### Online Code Execution
- Judge0 integration
- Multiple programming language support
- Run custom test cases
- Submit solutions
- Runtime and memory statistics

### Problem Management
- Create and manage problems
- Tags and categories
- Constraints
- Sample test cases
- Hidden evaluation test cases

### User Dashboard
- Submission history
- Solved problems
- Progress tracking
- User profile

### Community
- Problem discussions
- Editorials / Solutions
- Comments

---

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis

### Code Execution
- Judge0

### Authentication
- JWT
- OAuth2

### Containerization
- Docker
- Docker Compose

### AI
- Large Language Models (LLMs)
- Prompt Engineering

---

## High-Level Architecture

```
                Client
                   │
                   ▼
              FastAPI API
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   PostgreSQL    Redis     Judge0
                             │
                             ▼
                    Code Execution Workers
```

---


